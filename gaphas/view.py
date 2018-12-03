"""
This module contains everything to display a Canvas on a screen.
"""
from __future__ import absolute_import
from __future__ import division

from builtins import map
from builtins import object

from cairo import Matrix
from gi.repository import Gtk, GObject, Gdk

from .canvas import Context
from .decorators import AsyncIO
from .decorators import nonrecursive
from .geometry import Rectangle, distance_point_point_fast
from .painter import DefaultPainter, BoundingBoxPainter
from .quadtree import Quadtree
from .tool import DefaultTool

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = Gdk.CursorType.LEFT_PTR


class View(object):
    """
    View class for gaphas.Canvas objects.
    """

    def __init__(self, canvas=None):
        self._matrix = Matrix()
        self._painter = DefaultPainter(self)
        self._bounding_box_painter = BoundingBoxPainter(self)

        # Handling selections.
        # TODO: Move this to a context?
        self._selected_items = set()
        self._focused_item = None
        self._hovered_item = None
        self._dropzone_item = None

        self._qtree = Quadtree()
        self._bounds = Rectangle(0, 0, 0, 0)

        self._canvas = None
        if canvas:
            self._set_canvas(canvas)

    matrix = property(lambda s: s._matrix, doc="Canvas to view transformation matrix")

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        """
        if self._canvas:
            self._qtree.clear()
            self._selected_items.clear()
            self._focused_item = None
            self._hovered_item = None
            self._dropzone_item = None

        self._canvas = canvas

    canvas = property(lambda s: s._canvas, _set_canvas)

    def emit(self, *args, **kwargs):
        """
        Placeholder method for signal emission functionality.
        """
        pass

    def queue_draw_item(self, *items):
        """
        Placeholder for item redraw queueing.
        """
        pass

    def select_item(self, item):
        """
        Select an item. This adds @item to the set of selected items.
        """
        self.queue_draw_item(item)
        if item not in self._selected_items:
            self._selected_items.add(item)
            self.emit("selection-changed", self._selected_items)

    def unselect_item(self, item):
        """
        Unselect an item.
        """
        self.queue_draw_item(item)
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.emit("selection-changed", self._selected_items)

    def select_all(self):
        for item in self.canvas.get_all_items():
            self.select_item(item)

    def unselect_all(self):
        """
        Clearing the selected_item also clears the focused_item.
        """
        self.queue_draw_item(*self._selected_items)
        self._selected_items.clear()
        self.focused_item = None
        self.emit("selection-changed", self._selected_items)

    selected_items = property(
        lambda s: s._selected_items,
        select_item,
        unselect_all,
        "Items selected by the view",
    )

    def _set_focused_item(self, item):
        """
        Set the focused item, this item is also added to the
        selected_items set.
        """
        if not item is self._focused_item:
            self.queue_draw_item(self._focused_item, item)

        if item:
            self.select_item(item)
        if item is not self._focused_item:
            self._focused_item = item
            self.emit("focus-changed", item)

    def _del_focused_item(self):
        """
        Items that loose focus remain selected.
        """
        self._set_focused_item(None)

    focused_item = property(
        lambda s: s._focused_item,
        _set_focused_item,
        _del_focused_item,
        "The item with focus (receives key events a.o.)",
    )

    def _set_hovered_item(self, item):
        """
        Set the hovered item.
        """
        if item is not self._hovered_item:
            self.queue_draw_item(self._hovered_item, item)
            self._hovered_item = item
            self.emit("hover-changed", item)

    def _del_hovered_item(self):
        """
        Unset the hovered item.
        """
        self._set_hovered_item(None)

    hovered_item = property(
        lambda s: s._hovered_item,
        _set_hovered_item,
        _del_hovered_item,
        "The item directly under the mouse pointer",
    )

    def _set_dropzone_item(self, item):
        """
        Set dropzone item.
        """
        if item is not self._dropzone_item:
            self.queue_draw_item(self._dropzone_item, item)
            self._dropzone_item = item
            self.emit("dropzone-changed", item)

    def _del_dropzone_item(self):
        """
        Unset dropzone item.
        """
        self._set_dropzone_item(None)

    dropzone_item = property(
        lambda s: s._dropzone_item,
        _set_dropzone_item,
        _del_dropzone_item,
        "The item which can group other items",
    )

    def _set_painter(self, painter):
        """
        Set the painter to use. Painters should implement painter.Painter.
        """
        self._painter = painter
        painter.set_view(self)
        self.emit("painter-changed")

    painter = property(lambda s: s._painter, _set_painter)

    def _set_bounding_box_painter(self, painter):
        """
        Set the painter to use for bounding box calculations.
        """
        self._bounding_box_painter = painter
        painter.set_view(self)
        self.emit("painter-changed")

    bounding_box_painter = property(
        lambda s: s._bounding_box_painter, _set_bounding_box_painter
    )

    def get_item_at_point(self, pos, selected=True):
        """
        Return the topmost item located at ``pos`` (x, y).

        Parameters:
         - selected: if False returns first non-selected item
        """
        items = self._qtree.find_intersect((pos[0], pos[1], 1, 1))
        for item in self._canvas.sort(items, reverse=True):
            if not selected and item in self.selected_items:
                continue  # skip selected items

            v2i = self.get_matrix_v2i(item)
            ix, iy = v2i.transform_point(*pos)
            item_distance = item.point((ix, iy))
            if item_distance is None:
                print("Item distance is None for {}".format(item))
                continue
            if item_distance < 0.5:
                return item
        return None

    def get_handle_at_point(self, pos, distance=6):
        """
        Look for a handle at ``pos`` and return the
        tuple (item, handle).
        """

        def find(item):
            """ Find item's handle at pos """
            v2i = self.get_matrix_v2i(item)
            d = distance_point_point_fast(v2i.transform_distance(0, distance))
            x, y = v2i.transform_point(*pos)

            for h in item.handles():
                if not h.movable:
                    continue
                hx, hy = h.pos
                if -d < (hx - x) < d and -d < (hy - y) < d:
                    return h

        # The focused item is the prefered item for handle grabbing
        if self.focused_item:
            h = find(self.focused_item)
            if h:
                return self.focused_item, h

        # then try hovered item
        if self.hovered_item:
            h = find(self.hovered_item)
            if h:
                return self.hovered_item, h

        # Last try all items, checking the bounding box first
        x, y = pos
        items = self.get_items_in_rectangle(
            (x - distance, y - distance, distance * 2, distance * 2), reverse=True
        )

        found_item, found_h = None, None
        for item in items:
            h = find(item)
            if h:
                return item, h
        return None, None

    def get_port_at_point(self, vpos, distance=10, exclude=None):
        """
        Find item with port closest to specified position.

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
        items = self.get_items_in_rectangle(rect, reverse=True)
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

    def get_items_in_rectangle(self, rect, intersect=True, reverse=False):
        """
        Return the items in the rectangle 'rect'.
        Items are automatically sorted in canvas' processing order.
        """
        if intersect:
            items = self._qtree.find_intersect(rect)
        else:
            items = self._qtree.find_inside(rect)
        return self._canvas.sort(items, reverse=reverse)

    def select_in_rectangle(self, rect):
        """
        Select all items who have their bounding box within the
        rectangle @rect.
        """
        items = self._qtree.find_inside(rect)
        list(map(self.select_item, items))

    def zoom(self, factor):
        """
        Zoom in/out by factor @factor.
        """
        # TODO: should the scale factor be clipped?
        self._matrix.scale(factor, factor)

        # Make sure everything's updated
        # map(self.update_matrix, self._canvas.get_all_items())
        self.request_update((), self._canvas.get_all_items())

    def set_item_bounding_box(self, item, bounds):
        """
        Update the bounding box of the item.

        ``bounds`` is in view coordinates.

        Coordinates are calculated back to item coordinates, so
        matrix-only updates can occur.
        """
        v2i = self.get_matrix_v2i(item).transform_point
        ix0, iy0 = v2i(bounds.x, bounds.y)
        ix1, iy1 = v2i(bounds.x1, bounds.y1)
        self._qtree.add(item=item, bounds=bounds, data=(ix0, iy0, ix1, iy1))

    def get_item_bounding_box(self, item):
        """
        Get the bounding box for the item, in view coordinates.
        """
        return self._qtree.get_bounds(item)

    bounding_box = property(lambda s: s._bounds)

    def update_bounding_box(self, cr, items=None):
        """
        Update the bounding boxes of the canvas items for this view,
        in canvas coordinates.
        """
        painter = self._bounding_box_painter
        if items is None:
            items = self.canvas.get_all_items()

        # The painter calls set_item_bounding_box() for each rendered item.
        painter.paint(Context(cairo=cr, items=items, area=None))

        # Update the view's bounding box with the rest of the items
        self._bounds = Rectangle(*self._qtree.soft_bounds)

    def paint(self, cr):
        self._painter.paint(
            Context(cairo=cr, items=self.canvas.get_all_items(), area=None)
        )

    def get_matrix_i2v(self, item):
        """
        Get Item to View matrix for ``item``.
        """
        if self not in item._matrix_i2v:
            self.update_matrix(item)
        return item._matrix_i2v[self]

    def get_matrix_v2i(self, item):
        """
        Get View to Item matrix for ``item``.
        """
        if self not in item._matrix_v2i:
            self.update_matrix(item)
        return item._matrix_v2i[self]

    def update_matrix(self, item):
        """
        Update item matrices related to view.
        """
        matrix_i2c = self.canvas.get_matrix_i2c(item)
        try:
            i2v = matrix_i2c.multiply(self._matrix)
        except AttributeError:
            # Fall back to old behaviour
            i2v = matrix_i2c * self._matrix

        item._matrix_i2v[self] = i2v

        v2i = Matrix(*i2v)
        v2i.invert()
        item._matrix_v2i[self] = v2i

    def _clear_matrices(self):
        """
        Clear registered data in Item's _matrix{i2c|v2i} attributes.
        """
        for item in self.canvas.get_all_items():
            try:
                del item._matrix_i2v[self]
                del item._matrix_v2i[self]
            except KeyError:
                pass


class GtkView(Gtk.DrawingArea, Gtk.Scrollable, View):
    # NOTE: Inherit from GTK+ class first, otherwise BusErrors may occur!
    """
    GTK+ widget for rendering a canvas.Canvas to a screen.  The view
    uses Tools from `tool.py` to handle events and Painters from
    `painter.py` to draw. Both are configurable.

    The widget already contains adjustment objects (`hadjustment`,
    `vadjustment`) to be used for scrollbars.

    This view registers itself on the canvas, so it will receive
    update events.
    """

    # Just defined a name to make GTK register this class.
    __gtype_name__ = "GaphasView"

    # Signals: emited after the change takes effect.
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

        self.connect("size-allocate", self.on_size_allocate)
        self.connect("draw", self.on_draw)
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
            | Gdk.EventMask.SCROLL_MASK
        )

        self._hadjustment = None
        self._vadjustment = None
        self._hadjustment_handler_id = None
        self._vadjustment_handler_id = None
        self._hscroll_policy = None
        self._vscroll_policy = None

        self._set_tool(DefaultTool())

    def do_get_property(self, prop):
        if prop.name == "hadjustemnet":
            return self._hadjustment
        elif prop.name == "vadjustment":
            return self._vadjustment
        elif prop.name == "hscroll-policy":
            return self._hscroll_policy
        elif prop.name == "vscroll-policy":
            return self._vscroll_policy
        else:
            raise AttributeError("Unknown property %s" % prop.name)

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
            raise AttributeError("Unknown property %s" % prop.name)

    def emit(self, *args, **kwargs):
        """
        Delegate signal emissions to the DrawingArea (=GTK+)
        """
        Gtk.DrawingArea.emit(self, *args, **kwargs)

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        This extends the behaviour of View.canvas.
        The view is also registered.
        """
        if self._canvas:
            self._clear_matrices()
            self._canvas.unregister_view(self)

        super(GtkView, self)._set_canvas(canvas)

        if self._canvas:
            self._canvas.register_view(self)
            self.request_update(self._canvas.get_all_items())
        self.queue_draw_refresh()

    canvas = property(lambda s: s._canvas, _set_canvas)

    def _set_tool(self, tool):
        """
        Set the tool to use. Tools should implement tool.Tool.
        """
        self._tool = tool
        tool.set_view(self)
        self.emit("tool-changed")

    tool = property(lambda s: s._tool, _set_tool)

    hadjustment = property(lambda s: s._hadjustment)

    vadjustment = property(lambda s: s._vadjustment)

    def zoom(self, factor):
        """
        Zoom in/out by factor ``factor``.
        """
        super(GtkView, self).zoom(factor)
        self.queue_draw_refresh()

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
        if v in c:
            u = c
        else:
            u = c + v

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
            self._vadjustment.set_value(v.y)
            self._vadjustment.set_lower(u.y)
            self._vadjustment.set_upper(u.y1)
            self._vadjustment.set_step_increment(ah // 10)
            self._vadjustment.set_page_increment(ah)
            self._vadjustment.set_page_size(ah)

    def queue_draw_item(self, *items):
        """
        Like ``DrawingArea.queue_draw_area``, but use the bounds of
        the item as update areas. Of course with a pythonic flavor:
        update any number of items at once.

        TODO: Should we also create a (sorted) list of items that need
        redrawal?
        """
        get_bounds = self._qtree.get_bounds
        items = [_f for _f in items if _f]
        try:
            # create a copy, otherwise we'll change the original rectangle
            bounds = Rectangle(*get_bounds(items[0]))
            for item in items[1:]:
                bounds += get_bounds(item)
            self.queue_draw_area(*bounds)
        except IndexError:
            pass
        except KeyError:
            pass  # No bounds calculated yet? bummer.

    def queue_draw_area(self, x, y, w, h):
        """
        Wrap draw_area to convert all values to ints.
        """
        try:
            super(GtkView, self).queue_draw_area(int(x), int(y), int(w + 1), int(h + 1))
        except OverflowError:
            # Okay, now the zoom factor is very large or something
            a = self.get_allocation()
            super(GtkView, self).queue_draw_area(0, 0, a.width, a.height)

    def queue_draw_refresh(self):
        """
        Redraw the entire view.
        """
        a = self.get_allocation()
        super(GtkView, self).queue_draw_area(0, 0, a.width, a.height)

    def request_update(self, items, matrix_only_items=(), removed_items=()):
        """
        Request update for items. Items will get a full update
        treatment, while ``matrix_only_items`` will only have their
        bounding box recalculated.
        """
        if items:
            self._dirty_items.update(items)
        if matrix_only_items:
            self._dirty_matrix_items.update(matrix_only_items)

        # Remove removed items:
        if removed_items:
            self._dirty_items.difference_update(removed_items)
            self.queue_draw_item(*removed_items)

            for item in removed_items:
                self._qtree.remove(item)
                self.selected_items.discard(item)

            if self.focused_item in removed_items:
                self.focused_item = None
            if self.hovered_item in removed_items:
                self.hovered_item = None
            if self.dropzone_item in removed_items:
                self.dropzone_item = None

        self.update()

    @AsyncIO(single=True)
    def update(self):
        """
        Update view status according to the items updated by the canvas.
        """
        if not self.get_window():
            return

        dirty_items = self._dirty_items
        dirty_matrix_items = self._dirty_matrix_items

        try:
            self.queue_draw_item(*dirty_items)

            # Mark old bb section for update
            self.queue_draw_item(*dirty_matrix_items)
            for i in dirty_matrix_items:
                if i not in self._qtree:
                    dirty_items.add(i)
                    self.update_matrix(i)
                    continue

                self.update_matrix(i)

                if i not in dirty_items:
                    # Only matrix has changed, so calculate new bb based
                    # on quadtree data (= bb in item coordinates).
                    bounds = self._qtree.get_data(i)
                    i2v = self.get_matrix_i2v(i).transform_point
                    x0, y0 = i2v(bounds[0], bounds[1])
                    x1, y1 = i2v(bounds[2], bounds[3])
                    vbounds = Rectangle(x0, y0, x1=x1, y1=y1)
                    self._qtree.add(i, vbounds, bounds)

            self.queue_draw_item(*dirty_matrix_items)

            # Request bb recalculation for all 'really' dirty items
            self.update_bounding_box(set(dirty_items))
        finally:
            self._dirty_items.clear()
            self._dirty_matrix_items.clear()

    @AsyncIO(single=False)
    def update_bounding_box(self, items):
        """
        Update bounding box is not necessary.
        """
        cr = self.get_window().cairo_create()

        cr.save()
        cr.rectangle(0, 0, 0, 0)
        cr.clip()
        try:
            super(GtkView, self).update_bounding_box(cr, items)
        finally:
            cr.restore()
        self.queue_draw_item(*items)
        self.update_adjustments()

    @nonrecursive
    def do_size_allocate(self, allocation):
        """
        Allocate the widget size ``(x, y, width, height)``.
        """
        Gtk.DrawingArea.do_size_allocate(self, allocation)
        self.set_allocation(allocation)
        self.update_adjustments(allocation)
        self._qtree.resize((0, 0, allocation.width, allocation.height))

    def on_size_allocate(self, widget, allocation):
        pass

    def do_realize(self):
        Gtk.DrawingArea.do_realize(self)

        # Ensure updates are propagated
        self._canvas.register_view(self)

        if self._canvas:
            self.request_update(self._canvas.get_all_items())

    def do_unrealize(self):
        if self.canvas:
            # Although Item._matrix_{i2v|v2i} keys are automatically removed
            # (weak refs), better do it explicitly to be sure.
            self._clear_matrices()
        self._qtree.clear()

        self._dirty_items.clear()
        self._dirty_matrix_items.clear()

        self._canvas.unregister_view(self)

        Gtk.DrawingArea.do_unrealize(self)

    def on_draw(self, widget, ctx):
        """
        Render canvas to the screen.
        """
        if not self._canvas:
            return

        cr = self.get_window().cairo_create()

        allocation = self.get_allocation()
        x = allocation.x
        y = allocation.y
        w = allocation.width
        h = allocation.height

        # Draw no more than necessary.
        cr.rectangle(x, y, w, h)
        cr.clip()

        area = Rectangle(x, y, width=w, height=h)
        self._painter.paint(
            Context(cairo=cr, items=self.get_items_in_rectangle(area), area=area)
        )

        if DEBUG_DRAW_BOUNDING_BOX:
            cr.save()
            cr.identity_matrix()
            cr.set_source_rgb(0, 0.8, 0)
            cr.set_line_width(1.0)
            b = self._bounds
            cr.rectangle(b[0], b[1], b[2], b[3])
            cr.stroke()
            cr.restore()

        # Draw Quadtree structure
        if DEBUG_DRAW_QUADTREE:

            def draw_qtree_bucket(bucket):
                cr.rectangle(*bucket.bounds)
                cr.stroke()
                for b in bucket._buckets:
                    draw_qtree_bucket(b)

            cr.set_source_rgb(0, 0, 0.8)
            cr.set_line_width(1.0)
            draw_qtree_bucket(self._qtree._bucket)

        return False

    def do_event(self, event):
        """
        Handle GDK events. Events are delegated to a `tool.Tool`.
        """
        if self._tool:
            return self._tool.handle(event) and True or False
        return False

    def on_adjustment_changed(self, adj):
        """
        Change the transformation matrix of the view to reflect the
        value of the x/y adjustment (scrollbar).
        """
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
        self._matrix *= m

        # Force recalculation of the bounding boxes:
        self.request_update((), self._canvas.get_all_items())

        self.queue_draw_refresh()


# vim: sw=4:et:ai
