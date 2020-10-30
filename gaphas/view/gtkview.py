"""This module contains everything to display a Canvas on a screen."""

from typing import Optional, Set, Tuple

import cairo
from gi.repository import Gdk, GLib, GObject, Gtk

from gaphas.canvas import Canvas, instant_cairo_context
from gaphas.decorators import AsyncIO
from gaphas.geometry import Rectangle, distance_point_point_fast
from gaphas.item import Item
from gaphas.matrix import Matrix
from gaphas.painter import BoundingBoxPainter, DefaultPainter, ItemPainter, Painter
from gaphas.position import Position
from gaphas.quadtree import Quadtree
from gaphas.tool import DefaultTool
from gaphas.view.scrolling import Scrolling
from gaphas.view.selection import Selection

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = Gdk.CursorType.LEFT_PTR

EVENT_MASK = (
    Gdk.EventMask.BUTTON_PRESS_MASK
    | Gdk.EventMask.BUTTON_RELEASE_MASK
    | Gdk.EventMask.POINTER_MOTION_MASK
    | Gdk.EventMask.KEY_PRESS_MASK
    | Gdk.EventMask.KEY_RELEASE_MASK
    | Gdk.EventMask.SCROLL_MASK
    | Gdk.EventMask.STRUCTURE_MASK
)


class GtkView(Gtk.DrawingArea, Gtk.Scrollable):
    """GTK+ widget for rendering a canvas.Canvas to a screen.  The view uses
    Tools to handle events and Painters to draw. Both are configurable.

    The widget already contains adjustment objects (`hadjustment`,
    `vadjustment`) to be used for scrollbars.

    This view registers itself on the canvas, so it will receive
    update events.
    """

    # Just defined a name to make GTK register this class.
    __gtype_name__ = "GaphasView"

    # Signals: emitted after the change takes effect.
    __gsignals__ = {
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

    def __init__(self, canvas: Optional[Canvas] = None):
        Gtk.DrawingArea.__init__(self)

        self._dirty_items: Set[Item] = set()
        self._dirty_matrix_items: Set[Item] = set()

        self._back_buffer: Optional[cairo.Surface] = None
        self._back_buffer_needs_resizing = True

        self.set_can_focus(True)
        self.add_events(EVENT_MASK)

        def alignment_updated(matrix):
            assert self._canvas
            self._matrix *= matrix  # type: ignore[operator]

            # Force recalculation of the bounding boxes:
            self.request_update((), self._canvas.get_all_items())

        self._scrolling = Scrolling(alignment_updated)

        self._selection = Selection()

        self._matrix = Matrix()
        self._painter: Painter = DefaultPainter(self)
        self._bounding_box_painter: Painter = BoundingBoxPainter(
            ItemPainter(self.selection), self.bounding_box_updater  # type: ignore[attr-defined]
        )

        self._qtree: Quadtree[Item, Tuple[float, float, float, float]] = Quadtree()

        self._canvas: Optional[Canvas] = None
        if canvas:
            self._set_canvas(canvas)

        def redraw(selection, item, signal_name):
            self.queue_redraw()

        self._selection.connect("selection-changed", redraw, "selection-changed")
        self._selection.connect("focus-changed", redraw, "focus-changed")
        self._selection.connect("hover-changed", redraw, "hover-changed")
        self._selection.connect("dropzone-changed", redraw, "dropzone-changed")

        self._set_tool(DefaultTool())

    def do_get_property(self, prop):
        return self._scrolling.get_property(prop)

    def do_set_property(self, prop, value):
        self._scrolling.set_property(prop, value)

    @property
    def matrix(self) -> Matrix:
        """Canvas to view transformation matrix."""
        return self._matrix

    def get_matrix_i2v(self, item):
        """Get Item to View matrix for ``item``."""
        return item.matrix_i2c.multiply(self._matrix)

    def get_matrix_v2i(self, item):
        """Get View to Item matrix for ``item``."""
        m = self.get_matrix_i2v(item)
        m.invert()
        return m

    def _set_canvas(self, canvas: Optional[Canvas]):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.

        The view is also registered.
        """
        if self._canvas:
            self._canvas.unregister_view(self)
            self._selection.clear()
            self._qtree.clear()

        self._canvas = canvas

        if self._canvas:
            self._canvas.register_view(self)
            self.request_update(self._canvas.get_all_items())

    canvas = property(lambda s: s._canvas, _set_canvas)

    def _set_painter(self, painter: Painter):
        """Set the painter to use.

        Painters should implement painter.Painter.
        """
        self._painter = painter
        self.emit("painter-changed")

    painter = property(lambda s: s._painter, _set_painter)

    def _set_bounding_box_painter(self, painter):
        """Set the painter to use for bounding box calculations."""
        self._bounding_box_painter = painter
        self.emit("painter-changed")

    bounding_box_painter = property(
        lambda s: s._bounding_box_painter, _set_bounding_box_painter
    )

    selection = property(lambda s: s._selection)

    bounding_box = property(lambda s: Rectangle(*s._qtree.soft_bounds))

    def _set_tool(self, tool):
        """Set the tool to use.

        Tools should implement tool.Tool.
        """
        self._tool = tool
        tool.set_view(self)
        self.emit("tool-changed")

    tool = property(lambda s: s._tool, _set_tool)

    hadjustment = property(lambda s: s._scrolling.hadjustment)

    vadjustment = property(lambda s: s._scrolling.vadjustment)

    def zoom(self, factor):
        """Zoom in/out by factor ``factor``."""
        assert self._canvas
        self.matrix.scale(factor, factor)
        self.request_update((), self._canvas.get_all_items())

    def select_in_rectangle(self, rect):
        """Select all items who have their bounding box within the rectangle.

        @rect.
        """
        for item in self._qtree.find_inside(rect):
            self._selection.select_items(item)

    def get_items_in_rectangle(self, rect):
        """Return the items in the rectangle 'rect'.

        Items are automatically sorted in canvas' processing order.
        """
        assert self._canvas
        items = self._qtree.find_intersect(rect)
        return self._canvas.sort(items)

    def get_item_at_point(self, pos, selected=True):
        """Return the topmost item located at ``pos`` (x, y).

        Parameters:
         - selected: if False returns first non-selected item
        """
        assert self._canvas
        items = self._qtree.find_intersect((pos[0], pos[1], 1, 1))
        for item in reversed(self._canvas.sort(items)):
            if not selected and item in self.selection.selected_items:
                continue  # skip selected items

            v2i = self.get_matrix_v2i(item)
            ix, iy = v2i.transform_point(*pos)
            item_distance = item.point(Position((ix, iy)))
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

    def get_port_at_point(self, vpos, distance=10, exclude=None):
        """Find item with port closest to specified position.

        List of items to be ignored can be specified with `exclude`
        parameter.

        Tuple is returned

        - found item
        - closest, connectable port
        - closest point on found port (in view coordinates)

        :Parameters:
         vpos
            Position specified in view coordinates.
         distance
            Max distance from point to a port (default 10)
         exclude
            Set of items to ignore.
        """
        v2i = self.get_matrix_v2i
        vx, vy = vpos

        max_dist = distance
        port = None
        glue_pos = None
        item = None

        rect = (vx - distance, vy - distance, distance * 2, distance * 2)
        items = reversed(self.get_items_in_rectangle(rect))
        for i in items:
            if i in exclude:
                continue
            for p in i.ports():
                if not p.connectable:
                    continue

                ix, iy = v2i(i).transform_point(vx, vy)
                pg, d = p.glue((ix, iy))

                if d >= max_dist:
                    continue

                max_dist = d
                item = i
                port = p

                # transform coordinates from connectable item space to view
                # space
                i2v = self.get_matrix_i2v(i).transform_point
                glue_pos = i2v(*pg)

        return item, port, glue_pos

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
            self._dirty_matrix_items.difference_update(removed_items)
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
        canvas = self.canvas
        if not canvas:
            return

        try:
            dirty_items = self._dirty_items
            dirty_matrix_items = self.all_dirty_matrix_items()

            self.canvas.update_now(dirty_items, dirty_matrix_items)

            dirty_items.update(self.update_qtree(dirty_items, dirty_matrix_items))
            self.update_bounding_box(dirty_items)
            self._scrolling.update_adjustments(
                self.get_allocation(), self._qtree.soft_bounds
            )
            self.update_back_buffer()
        finally:
            self._dirty_items.clear()
            self._dirty_matrix_items.clear()

    def all_dirty_matrix_items(self):
        """Recalculate matrices of the items. Items' children matrices are
        recalculated, too.

        Return items, which matrices were recalculated.
        """
        canvas = self._canvas
        if not canvas:
            return

        def update_matrices(items):
            assert canvas
            for item in items:
                parent = canvas.get_parent(item)
                if parent is not None and parent in items:
                    # item's matrix will be updated thanks to parent's matrix update
                    continue

                yield item

                yield from update_matrices(set(canvas.get_children(item)))

        return set(update_matrices(self._dirty_matrix_items))

    def update_qtree(self, dirty_items, dirty_matrix_items):
        for i in dirty_matrix_items:
            if i not in self._qtree:
                yield i
            elif i not in dirty_items:
                # Only matrix has changed, so calculate new bounding box
                # based on quadtree data (= bb in item coordinates).
                bounds = self._qtree.get_data(i)
                i2v = self.get_matrix_i2v(i).transform_point
                x0, y0 = i2v(bounds[0], bounds[1])
                x1, y1 = i2v(bounds[2], bounds[3])
                vbounds = Rectangle(x0, y0, x1=x1, y1=y1)
                self._qtree.add(i, vbounds.tuple(), bounds)

    def get_item_bounding_box(self, item):
        """Get the bounding box for the item, in view coordinates."""
        return self._qtree.get_bounds(item)

    def bounding_box_updater(self, item, bounds):
        """Update the bounding box of the item.

        ``bounds`` is in view coordinates.

        Coordinates are calculated back to item coordinates, so
        matrix-only updates can occur.
        """
        v2i = self.get_matrix_v2i(item).transform_point
        ix0, iy0 = v2i(bounds.x, bounds.y)
        ix1, iy1 = v2i(bounds.x1, bounds.y1)
        self._qtree.add(item=item, bounds=bounds, data=(ix0, iy0, ix1, iy1))

    def update_bounding_box(self, items):
        """Update the bounding boxes of the canvas items for this view, in
        canvas coordinates."""
        cr = (
            cairo.Context(self._back_buffer)
            if self._back_buffer
            else instant_cairo_context()
        )

        cr.set_matrix(
            self.matrix.to_cairo()
        )  # Need it, so I can size things like handles
        cr.save()
        cr.rectangle(0, 0, 0, 0)
        cr.clip()
        try:
            painter = self._bounding_box_painter
            if items is None:
                items = self.canvas.get_all_items()

            for item, bounds in painter.paint(items, cr).items():
                v2i = self.get_matrix_v2i(item).transform_point
                ix0, iy0 = v2i(bounds.x, bounds.y)
                ix1, iy1 = v2i(bounds.x1, bounds.y1)
                self._qtree.add(item=item, bounds=bounds, data=(ix0, iy0, ix1, iy1))
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

            assert self._back_buffer
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

            cr.set_matrix(self.matrix.to_cairo())
            cr.save()
            self.painter.paint(items, cr)
            cr.restore()

            if DEBUG_DRAW_BOUNDING_BOX:
                for item in items:
                    try:
                        b = self.get_item_bounding_box(item)
                    except KeyError:
                        pass  # No bounding box right now..
                    else:
                        cr.save()
                        cr.identity_matrix()
                        cr.set_source_rgb(0.8, 0, 0)
                        cr.set_line_width(1.0)
                        cr.rectangle(*b)
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
        self._scrolling.update_adjustments(allocation, self._qtree.soft_bounds)
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
