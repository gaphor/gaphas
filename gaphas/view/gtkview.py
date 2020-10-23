"""This module contains everything to display a Canvas on a screen."""

import cairo
from gi.repository import Gdk, GLib, GObject, Gtk

from gaphas.canvas import Context, instant_cairo_context
from gaphas.decorators import AsyncIO
from gaphas.geometry import Rectangle, distance_point_point_fast
from gaphas.matrix import Matrix
from gaphas.tool import DefaultTool
from gaphas.view.selection import Selection
from gaphas.view.view import View

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = Gdk.CursorType.LEFT_PTR


class GtkView(Gtk.DrawingArea, Gtk.Scrollable, View):
    # NOTE: Inherit from GTK+ class first, otherwise BusErrors may occur!
    """GTK+ widget for rendering a canvas.Canvas to a screen.  The view uses
    Tools from `tool.py` to handle events and Painters from `painter.py` to
    draw. Both are configurable.

    The widget already contains adjustment objects (`hadjustment`,
    `vadjustment`) to be used for scrollbars.

    This view registers itself on the canvas, so it will receive
    update events.
    """

    # Just defined a name to make GTK register this class.
    __gtype_name__ = "GaphasView"

    # Signals: emitted after the change takes effect.
    __gsignals__ = {
        "dropzone-changed": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,),
        ),
        "hover-changed": (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
        "focus-changed": (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
        "selection-changed": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,),
        ),
        "tool-changed": (GObject.SignalFlags.RUN_LAST, None, ()),
        "painter-changed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    __gproperties__ = {
        "hscroll-policy": (
            Gtk.ScrollablePolicy,
            "hscroll-policy",
            "hscroll-policy",
            Gtk.ScrollablePolicy.MINIMUM,
            GObject.ParamFlags.READWRITE,
        ),
        "hadjustment": (
            Gtk.Adjustment,
            "hadjustment",
            "hadjustment",
            GObject.ParamFlags.READWRITE,
        ),
        "vscroll-policy": (
            Gtk.ScrollablePolicy,
            "vscroll-policy",
            "vscroll-policy",
            Gtk.ScrollablePolicy.MINIMUM,
            GObject.ParamFlags.READWRITE,
        ),
        "vadjustment": (
            Gtk.Adjustment,
            "vadjustment",
            "vadjustment",
            GObject.ParamFlags.READWRITE,
        ),
    }

    def __init__(self, canvas=None):
        Gtk.DrawingArea.__init__(self)

        self._dirty_items = set()
        self._dirty_matrix_items = set()

        View.__init__(self, canvas)

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.STRUCTURE_MASK
        )

        self._back_buffer = None
        self._back_buffer_needs_resizing = True
        self._hadjustment = None
        self._vadjustment = None
        self._hadjustment_handler_id = None
        self._vadjustment_handler_id = None
        self._hscroll_policy = None
        self._vscroll_policy = None

        self._selection = Selection()
        self._selection.connect(
            "selection-changed", self._forward_signal, "selection-changed"
        )
        self._selection.connect("focus-changed", self._forward_signal, "focus-changed")
        self._selection.connect("hover-changed", self._forward_signal, "hover-changed")
        self._selection.connect(
            "dropzone-changed", self._forward_signal, "dropzone-changed"
        )

        self._set_tool(DefaultTool())

    def _forward_signal(self, selection, item, signal_name):
        self.queue_redraw()
        self.emit(signal_name, item)

    def do_get_property(self, prop):
        if prop.name == "hadjustment":
            return self._hadjustment
        elif prop.name == "vadjustment":
            return self._vadjustment
        elif prop.name == "hscroll-policy":
            return self._hscroll_policy
        elif prop.name == "vscroll-policy":
            return self._vscroll_policy
        else:
            raise AttributeError(f"Unknown property {prop.name}")

    def do_set_property(self, prop, value):
        if prop.name == "hadjustment":
            if value is not None:
                self._hadjustment = value
                self._hadjustment_handler_id = self._hadjustment.connect(
                    "value-changed", self.on_adjustment_changed
                )
                self.update_adjustments()
        elif prop.name == "vadjustment":
            if value is not None:
                self._vadjustment = value
                self._vadjustment_handler_id = self._vadjustment.connect(
                    "value-changed", self.on_adjustment_changed
                )
                self.update_adjustments()
        elif prop.name == "hscroll-policy":
            self._hscroll_policy = value
        elif prop.name == "vscroll-policy":
            self._vscroll_policy = value
        else:
            raise AttributeError(f"Unknown property {prop.name}")

    def _set_painter(self, painter):
        """Set the painter to use.

        Painters should implement painter.Painter.
        """
        super()._set_painter(painter)
        self.emit("painter-changed")

    def _set_bounding_box_painter(self, painter):
        """Set the painter to use for bounding box calculations."""
        super()._set_bounding_box_painter(painter)
        self.emit("painter-changed")

    def emit(self, *args, **kwargs):
        """Delegate signal emissions to the DrawingArea (=GTK+)"""
        Gtk.DrawingArea.emit(self, *args, **kwargs)

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        This extends the behaviour of View.canvas.
        The view is also registered.
        """
        if self._canvas:
            self._canvas.unregister_view(self)
            self._selection.clear()

        self._canvas = canvas

        super()._set_canvas(canvas)

        if self._canvas:
            self._canvas.register_view(self)
            self.request_update(self._canvas.get_all_items())
        self.queue_redraw()

    canvas = property(lambda s: s._canvas, _set_canvas)

    selection = property(lambda s: s._selection)

    def _set_tool(self, tool):
        """Set the tool to use.

        Tools should implement tool.Tool.
        """
        self._tool = tool
        tool.set_view(self)
        self.emit("tool-changed")

    tool = property(lambda s: s._tool, _set_tool)

    hadjustment = property(lambda s: s._hadjustment)

    vadjustment = property(lambda s: s._vadjustment)

    def zoom(self, factor):
        """Zoom in/out by factor ``factor``."""
        assert self._canvas
        self.matrix.scale(factor, factor)
        self.request_update((), self._canvas.get_all_items())
        self.queue_redraw()

    def select_in_rectangle(self, rect):
        """Select all items who have their bounding box within the rectangle.

        @rect.
        """
        for item in self._qtree.find_inside(rect):
            self._selection.select_items(item)

    def get_item_at_point(self, pos, selected=True):
        """Return the topmost item located at ``pos`` (x, y).

        Parameters:
         - selected: if False returns first non-selected item
        """
        assert self._canvas
        items = self._qtree.find_intersect((pos[0], pos[1], 1, 1))
        for item in reversed(self._canvas.sort(items)):
            if not selected and item in self.selected_items:
                continue  # skip selected items

            v2i = self.get_matrix_v2i(item)
            ix, iy = v2i.transform_point(*pos)
            item_distance = item.point((ix, iy))
            if item_distance is None:
                print(f"Item distance is None for {item}")
                continue
            if item_distance < 0.5:
                return item
        return None

    def get_handle_at_point(self, pos, distance=6):
        """Look for a handle at ``pos`` and return the tuple (item, handle)."""

        def find(item):
            """Find item's handle at pos."""
            v2i = self.get_matrix_v2i(item)
            d = distance_point_point_fast(v2i.transform_distance(0, distance))
            x, y = v2i.transform_point(*pos)

            for h in item.handles():
                if not h.movable:
                    continue
                hx, hy = h.pos
                if -d < (hx - x) < d and -d < (hy - y) < d:
                    return h

        selection = self._selection

        # The focused item is the preferred item for handle grabbing
        if selection.focused_item:
            h = find(selection.focused_item)
            if h:
                return selection.focused_item, h

        # then try hovered item
        if selection.hovered_item:
            h = find(selection.hovered_item)
            if h:
                return selection.hovered_item, h

        # Last try all items, checking the bounding box first
        x, y = pos
        items = reversed(
            self.get_items_in_rectangle(
                (x - distance, y - distance, distance * 2, distance * 2)
            )
        )

        for item in items:
            h = find(item)
            if h:
                return item, h
        return None, None

    @AsyncIO(single=True)
    def update_adjustments(self, allocation=None):
        if not allocation:
            allocation = self.get_allocation()

        aw, ah = allocation.width, allocation.height

        hadjustment = self._hadjustment
        vadjustment = self._vadjustment

        # canvas limits (in view coordinates)
        c = Rectangle(*self._qtree.soft_bounds)

        # view limits
        v = Rectangle(0, 0, aw, ah)

        # union of these limits gives scrollbar limits
        u = c if v in c else c + v
        if hadjustment is None:
            self._hadjustment = Gtk.Adjustment.new(
                value=v.x,
                lower=u.x,
                upper=u.x1,
                step_increment=aw // 10,
                page_increment=aw,
                page_size=aw,
            )
        else:
            assert self._hadjustment
            self._hadjustment.set_value(v.x)
            self._hadjustment.set_lower(u.x)
            self._hadjustment.set_upper(u.x1)
            self._hadjustment.set_step_increment(aw // 10)
            self._hadjustment.set_page_increment(aw)
            self._hadjustment.set_page_size(aw)

        if vadjustment is None:
            self._vadjustment = Gtk.Adjustment.new(
                value=v.y,
                lower=u.y,
                upper=u.y1,
                step_increment=ah // 10,
                page_increment=ah,
                page_size=ah,
            )
        else:
            assert self._vadjustment
            self._vadjustment.set_value(v.y)
            self._vadjustment.set_lower(u.y)
            self._vadjustment.set_upper(u.y1)
            self._vadjustment.set_step_increment(ah // 10)
            self._vadjustment.set_page_increment(ah)
            self._vadjustment.set_page_size(ah)

    def queue_redraw(self):
        """Redraw the entire view."""
        self.update_back_buffer()

    def request_update(self, items, matrix_only_items=(), removed_items=()):
        """Request update for items.

        Items will get a full update treatment, while
        ``matrix_only_items`` will only have their bounding box
        recalculated.
        """
        if items:
            self._dirty_items.update(items)
        if matrix_only_items:
            self._dirty_matrix_items.update(matrix_only_items)

        # Remove removed items:
        if removed_items:
            selection = self._selection
            self._dirty_items.difference_update(removed_items)

            for item in removed_items:
                self._qtree.remove(item)
                selection.unselect_item(item)

            if selection.focused_item in removed_items:
                selection.set_focused_item(None)
            if selection.hovered_item in removed_items:
                selection.set_hovered_item(None)
            if selection.dropzone_item in removed_items:
                selection.set_dropzone_item(None)

        self.update()

    @AsyncIO(single=True)
    def update(self):
        """Update view status according to the items updated by the canvas."""

        if not self.get_window():
            return

        dirty_items = self._dirty_items
        dirty_matrix_items = self._dirty_matrix_items

        try:
            for i in dirty_matrix_items:
                if i not in self._qtree:
                    dirty_items.add(i)
                    continue

                if i not in dirty_items:
                    # Only matrix has changed, so calculate new bounding box
                    # based on quadtree data (= bb in item coordinates).
                    bounds = self._qtree.get_data(i)
                    i2v = self.get_matrix_i2v(i).transform_point
                    x0, y0 = i2v(bounds[0], bounds[1])
                    x1, y1 = i2v(bounds[2], bounds[3])
                    vbounds = Rectangle(x0, y0, x1=x1, y1=y1)
                    self._qtree.add(i, vbounds.tuple(), bounds)

            self.update_bounding_box(set(dirty_items))

            self.update_adjustments()

            self.update_back_buffer()
        finally:
            dirty_items.clear()
            self._dirty_matrix_items.clear()

    def update_bounding_box(self, items):
        cr = (
            cairo.Context(self._back_buffer)
            if self._back_buffer
            else instant_cairo_context()
        )

        cr.save()
        cr.rectangle(0, 0, 0, 0)
        cr.clip()
        try:
            super().update_bounding_box(cr, items)
        finally:
            cr.restore()

    @AsyncIO(single=True, priority=GLib.PRIORITY_HIGH_IDLE)
    def update_back_buffer(self):
        if self.canvas and self.get_window():
            if not self._back_buffer or self._back_buffer_needs_resizing:
                allocation = self.get_allocation()
                self._back_buffer = self.get_window().create_similar_surface(
                    cairo.Content.COLOR_ALPHA, allocation.width, allocation.height
                )
                self._back_buffer_needs_resizing = False

            allocation = self.get_allocation()
            cr = cairo.Context(self._back_buffer)

            cr.save()
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.paint()
            cr.restore()

            Gtk.render_background(
                self.get_style_context(), cr, 0, 0, allocation.width, allocation.height
            )

            items = self.get_items_in_rectangle(
                (0, 0, allocation.width, allocation.height)
            )

            self.painter.paint(Context(cairo=cr, items=items))

            if DEBUG_DRAW_BOUNDING_BOX:
                cr.save()
                cr.identity_matrix()
                cr.set_source_rgb(0, 0.8, 0)
                cr.set_line_width(1.0)
                b = self.bounding_box
                cr.rectangle(b[0], b[1], b[2], b[3])
                cr.stroke()
                cr.restore()

            if DEBUG_DRAW_QUADTREE:

                def draw_qtree_bucket(bucket):
                    cr.rectangle(*bucket.bounds)
                    cr.stroke()
                    for b in bucket._buckets:
                        draw_qtree_bucket(b)

                cr.set_source_rgb(0, 0, 0.8)
                cr.set_line_width(1.0)
                draw_qtree_bucket(self._qtree._bucket)

            self.get_window().invalidate_rect(allocation, True)

    def do_realize(self):
        Gtk.DrawingArea.do_realize(self)

        if self._canvas:
            # Ensure updates are propagated
            self._canvas.register_view(self)
            self.request_update(self._canvas.get_all_items())

    def do_unrealize(self):
        if self._canvas:
            self._canvas.unregister_view(self)

        self._qtree.clear()

        self._dirty_items.clear()
        self._dirty_matrix_items.clear()

        Gtk.DrawingArea.do_unrealize(self)

    def do_configure_event(self, event):
        allocation = self.get_allocation()
        self.update_adjustments(allocation)
        self._qtree.resize((0, 0, allocation.width, allocation.height))
        if self.get_window():
            self._back_buffer_needs_resizing = True
            self.update_back_buffer()
        else:
            self._back_buffer = None

        return False

    def do_draw(self, cr):
        """Render canvas to the screen."""
        if not self._canvas:
            return

        if not self._back_buffer:
            return

        cr.set_source_surface(self._back_buffer, 0, 0)
        cr.paint()

        return False

    def do_event(self, event):
        """Handle GDK events.

        Events are delegated to a `tool.Tool`.
        """
        if self._tool:
            return self._tool.handle(event) and True or False
        return False

    def on_adjustment_changed(self, adj):
        """Change the transformation matrix of the view to reflect the value of
        the x/y adjustment (scrollbar)."""
        assert self._canvas

        value = adj.get_value()
        if value == 0.0:
            return

        # Can not use self._matrix.translate(-value , 0) here, since
        # the translate method effectively does a m * self._matrix, which
        # will result in the translation being multiplied by the orig. matrix
        m = Matrix()
        if adj is self._hadjustment:
            m.translate(-value, 0)
        elif adj is self._vadjustment:
            m.translate(0, -value)
        self._matrix *= m  # type: ignore[operator]

        # Force recalculation of the bounding boxes:
        self.request_update((), self._canvas.get_all_items())

        self.queue_redraw()
