"""
This module contains everything to display a Canvas on a screen.
"""

__version__ = "$Revision$"
# $HeadURL$

import gobject
import gtk
from cairo import Matrix
from canvas import Context
from geometry import Rectangle
from quadtree import Quadtree
from tool import ToolContext, DefaultTool
from painter import DefaultPainter, BoundingBoxPainter
from decorators import async, PRIORITY_HIGH_IDLE
from decorators import nonrecursive
from gaphas.sort import Sorted

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False

# The default cursor (in case of a cursor reset)
DEFAULT_CURSOR = gtk.gdk.LEFT_PTR


class View(object):
    """
    View class for gaphas.Canvas objects. 
    """

    def __init__(self, canvas=None):
        self._canvas = canvas

        self._qtree = Quadtree()

        # Handling selections.
        self._selected_items = Sorted(canvas)
        self._focused_item = None
        self._hovered_item = None
        self._dropzone_item = None

        self._matrix = Matrix()
        self._painter = DefaultPainter()

        self._dirty_items = set()
        self._dirty_matrix_items = set()

    matrix = property(lambda s: s._matrix,
                      doc="Canvas to view transformation matrix")

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        """
        if self._canvas:
            self._qtree = Quadtree()

        self._canvas = canvas
        self._selected_items.canvas = canvas
        
        if self._canvas:
            self.request_update(self._canvas.get_all_items())

    canvas = property(lambda s: s._canvas, _set_canvas)

    def emit(self, args, **kwargs):
        """
        Placeholder method for signal emission functionality.
        """
        pass

    def select_item(self, item):
        """
        Select an item. This adds @item to the set of selected items. Do::

            del view.selected_items

        to clear the selected items list.
        """
        self.queue_draw_item(item)
        if item not in self._selected_items:
            self._selected_items.add(item)
            self.emit('selection-changed', self._selected_items)

    def unselect_item(self, item):
        """
        Unselect an item.
        """
        self.queue_draw_item(item)
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.emit('selection-changed', self._selected_items)

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
        self.emit('selection-changed', self._selected_items)

    selected_items = property(lambda s: s._selected_items,
                              select_item, unselect_all,
                              "Items selected by the view")

    def _set_focused_item(self, item):
        """
        Set the focused item, this item is also added to the selected_items
        set.
        """
        if not item is self._focused_item:
            self.queue_draw_item(self._focused_item, item)

        if item:
            self.selected_items = item #.add(item)
        if item is not self._focused_item:
            self._focused_item = item
            self.emit('focus-changed', item)

    def _del_focused_item(self):
        """
        Items that loose focus remain selected.
        """
        self.focused_item = None
        
    focused_item = property(lambda s: s._focused_item,
                            _set_focused_item, _del_focused_item,
                            "The item with focus (receives key events a.o.)")

    def _set_hovered_item(self, item):
        """
        Set the hovered item.
        """
        if not item is self._hovered_item:
            self.queue_draw_item(self._hovered_item, item)
        if item is not self._hovered_item:
            self._hovered_item = item
            self.emit('hover-changed', item)

    def _del_hovered_item(self):
        """
        Unset the hovered item.
        """
        self.hovered_item = None
        
    hovered_item = property(lambda s: s._hovered_item,
                            _set_hovered_item, _del_hovered_item,
                            "The item directly under the mouse pointer")


    def _set_dropzone_item(self, item):
        """
        Set dropzone item.
        """
        if item is not self._dropzone_item:
            self.queue_draw_item(self._dropzone_item, item)
            self._dropzone_item = item
            self.emit('dropzone-changed', item)


    def _del_dropzone_item(self):
        """
        Unset dropzone item.
        """
        self._dropzone_item = None


    dropzone_item = property(lambda s: s._dropzone_item,
            _set_dropzone_item, _del_dropzone_item,
            'The item which can group other items')


    def _set_painter(self, painter):
        """
        Set the painter to use. Painters should implement painter.Painter.
        """
        self._painter = painter
        self.emit('painter-changed')

    painter = property(lambda s: s._painter, _set_painter)

    def get_item_at_point(self, x, y, selected=True):
        """
        Return the topmost item located at (x, y).

        Parameters:
         - selected: if False returns first non-selected item
        """
        point = (x, y)
        items = self._qtree.find_intersect((x, y, 1, 1))
        for item in self._canvas.sorter.sort(items, reverse=True):
            if not selected and item in self.selected_items:
                continue  # skip selected items

            v2i = self.get_matrix_v2i(item)
            ix, iy = v2i.transform_point(x, y)
            if item.point(ix, iy) < 0.5:
                return item
        return None

    def select_in_rectangle(self, rect):
        """
        Select all items who have their bounding box within the
        rectangle @rect.
        """
        for item in self._canvas.get_all_items():
            if self.get_item_bounding_box(item) in rect:
                self.select_item(item)

    def zoom(self, factor):
        """
        Zoom in/out by factor @factor.
        """
        self._matrix.scale(factor, factor)

        # Make sure everything's updated
        map(self.update_matrix, self._canvas.get_all_items())
        self.request_update(self._canvas.get_all_items())

    def set_item_bounding_box(self, item, bounds):
        """
        Update the bounding box of the item (in canvas coordinates).

        Coordinates are calculated back to item coordinates, so matrix-only
        updates can occur.
        """
        # Converting from item to canvas coordinates doesn't work properly,
        # since items should take into account their child objects when
        # bounding boxes are calculated. Now, the child objects should not
        # be hindered by their own matrix settings.
        v2i = self.get_matrix_v2i(item).transform_point
        ix0, iy0 = v2i(bounds.x, bounds.y)
        ix1, iy1 = v2i(bounds.x1, bounds.y1)
        self._qtree.add(item=item, bounds=bounds, data=Rectangle(ix0, iy0, x1=ix1, y1=iy1))

        # Update bounding box of parent items where appropriate (only extent)
        parent = self.canvas.get_parent(item)
        if parent:
            try:
                parent_bounds = self._qtree.get_bounds(parent)
            except KeyError:
                pass # No bounds, do nothing
            else:
                if not bounds in parent_bounds:
                    self.set_item_bounding_box(parent, bounds + parent_bounds)

    def get_item_bounding_box(self, item):
        """
        Get the bounding box for the item, in canvas coordinates.
        """
        return self._qtree.get_bounds(item)

    def get_canvas_size(self):
        """
        The canvas size (width, height) in canvas coordinates, determined
        from the origin (0, 0).
        """
        inverse = Matrix(*self._matrix)
        inverse.invert()
        x, y, w, h = self._qtree.bounds
        ww, wh = inverse.transform_point(x + w, y + h)
        return self._matrix.transform_distance(ww, wh)

    bounding_box = property(lambda s: s._qtree.bounds)

    def update_bounding_box(self, cr, items=None):
        """
        Update the bounding boxes of the canvas items for this view, in 
        canvas coordinates.
        """
        painter = BoundingBoxPainter()
        if items is None:
            items = self.canvas.get_root_items()

        # The painter calls set_item_bounding_box() for each rendered item.
        painter.paint(Context(view=self,
                              cairo=cr,
                              items=items))

        # Update the view's bounding box with the rest of the items
        self._bounds = Rectangle(*self._qtree.autosize())

    def paint(self, cr):
        self._painter.paint(Context(view=self,
                                    cairo=cr,
                                    area=None))


    def get_matrix_i2v(self, item):
        return item._matrix_i2v[self]


    def get_matrix_v2i(self, item):
        return item._matrix_v2i[self]


    def update_matrix(self, item):
        """
        Update item matrices related to view.
        """
        i2v = item._matrix_i2v[self] = self._canvas.get_matrix_i2c(item) * self._matrix
        v2i = item._matrix_v2i[self] = Matrix(*i2v)
        v2i.invert()



# Map GDK events to tool methods
EVENT_HANDLERS = {
    gtk.gdk.BUTTON_PRESS: 'on_button_press',
    gtk.gdk.BUTTON_RELEASE: 'on_button_release',
    gtk.gdk._2BUTTON_PRESS: 'on_double_click',
    gtk.gdk._3BUTTON_PRESS: 'on_triple_click',
    gtk.gdk.MOTION_NOTIFY: 'on_motion_notify',
    gtk.gdk.KEY_PRESS: 'on_key_press',
    gtk.gdk.KEY_RELEASE: 'on_key_release'
}



class GtkView(gtk.DrawingArea, View):
    # NOTE: Ingerit from GTK+ class first, otherwise BusErrors may occur!
    """
    GTK+ widget for rendering a canvas.Canvas to a screen.
    The view uses Tools from tool.py to handle events and Painters
    from painter.py to draw. Both are configurable.
    """

    # just defined a name to make GTK register this entity.
    __gtype_name__ = 'GaphasView'
    
    # Signals: emited before the change takes effect.
    __gsignals__ = {
        'dropzone-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,)),
        'hover-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,)),
        'focus-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,)),
        'selection-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      (gobject.TYPE_PYOBJECT,)),
        'tool-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      ()),
        'painter-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                      ())
    }

    def __init__(self, canvas=None):
        super(GtkView, self).__init__()
        View.__init__(self)
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.KEY_PRESS_MASK
                        | gtk.gdk.KEY_RELEASE_MASK)

        self.hadjustment = gtk.Adjustment()
        self.vadjustment = gtk.Adjustment()

        self._tool = DefaultTool()
        self.canvas = canvas

        # Set background to white.
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FFF'))

        self._update_bounding_box = set()

    def emit(self, *args, **kwargs):
        """
        Delegate signal emissions to the DrawingArea (=GTK+)
        """
        gtk.DrawingArea.emit(self, *args, **kwargs)

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        This extends the behaviour of View.canvas.
        """
        if self._canvas:
            self._canvas.unregister_view(self)

        super(GtkView, self)._set_canvas(canvas)
        
        if self._canvas:
            self._canvas.register_view(self)

    canvas = property(lambda s: s._canvas, _set_canvas)

    def _set_tool(self, tool):
        """
        Set the tool to use. Tools should implement tool.Tool.
        """
        self._tool = tool
        self.emit('tool-changed')

    tool = property(lambda s: s._tool, _set_tool)

    def _set_hadjustment(self, adj):
        """
        Set horizontal adjustment object, for scrollbars.
        """
        #if self._hadjustment:
        #    self._hadjustment.disconnect(self.on_adjustment_changed)
        self._hadjustment = adj
        adj.connect('value_changed', self.on_adjustment_changed)

    hadjustment = property(lambda s: s._hadjustment, _set_hadjustment)

    def _set_vadjustment(self, adj):
        """
        Set vertical adjustment object, for scrollbars.
        """
        #if self._vadjustment:
        #    self._vadjustment.disconnect(self.on_adjustment_changed)
        self._vadjustment = adj
        adj.connect('value_changed', self.on_adjustment_changed)

    vadjustment = property(lambda s: s._vadjustment, _set_vadjustment)

    def zoom(self, factor):
        """
        Zoom in/out by factor @factor.
        """
        super(GtkView, self).zoom(factor)
        a = self.allocation
        super(GtkView, self).queue_draw_area(0, 0, a.width, a.height)

    def _update_adjustment(self, adjustment, value, canvas_size, viewport_size):
        """
        >>> v = GtkView()
        >>> a = gtk.Adjustment()
        >>> v._hadjustment = a
        >>> v._update_adjustment(a, 10, 100, 20)
        >>> a.page_size, a.page_increment, a.value
        (20.0, 20.0, 10.0)
        """
        size = min(canvas_size, viewport_size)
        canvas_size += viewport_size
        if size != adjustment.page_size or canvas_size != adjustment.upper:
            adjustment.page_size = size
            adjustment.page_increment = size
            adjustment.step_increment = size/10
            adjustment.upper = canvas_size
            adjustment.lower = 0
            adjustment.changed()
        
        value = max(0, min(value, canvas_size - size))
        if value != adjustment.value:
            adjustment.value = value
            adjustment.value_changed()

    def update_adjustments(self, allocation=None):
        """
        Update the allocation objects (for scrollbars).
        """
        if not allocation:
            allocation = self.allocation
        w, h = self.get_canvas_size()
        self._update_adjustment(self._hadjustment,
                                value = self._hadjustment.value,
                                canvas_size=w,
                                viewport_size=allocation.width)
        self._update_adjustment(self._vadjustment,
                                value = self._vadjustment.value,
                                canvas_size=h,
                                viewport_size=allocation.height)
        self._qtree.resize((0, 0, allocation.width, allocation.height))
        
    @async(single=False, priority=PRIORITY_HIGH_IDLE)
    def _idle_queue_draw_item(self, *items):
        self.queue_draw_item(*items)

    def queue_draw_item(self, *items):
        """
        Like DrawingArea.queue_draw_area, but use the bounds of the
        item as update areas. Of course with a pythonic flavor: update
        any number of items at once.
        """
        queue_draw_area = self.queue_draw_area
        get_item_bounding_box = self.get_item_bounding_box
        for item in items:
            try:
                queue_draw_area(*get_item_bounding_box(item))
            except KeyError:
                pass # No bounds calculated yet? bummer.

    def queue_draw_area(self, x, y, w, h):
        """
        Wrap draw_area to convert all values to ints.
        """
        super(GtkView, self).queue_draw_area(int(x), int(y), int(w+1), int(h+1))

    def request_update(self, items, matrix_only_items=()):
        """
        Request update for items. Items will get a full update treatment, while
        matrix_only_items will only have their bounding box recalculated.
        """
        if items:
            self._dirty_items.update(items)
        if matrix_only_items:
            self._dirty_matrix_items.update(matrix_only_items)
        self.update()

    @async(single=True, priority=PRIORITY_HIGH_IDLE)
    def update(self):
        """
        Update view status according to the items updated by the canvas.
        """
        if not self.window: return True

        dirty_items = self._dirty_items
        dirty_matrix_items = self._dirty_matrix_items

        # Add dirty_matrix_items' children to dirty_matrix_items set
        # For normal dirty_items this is taken care of in the boundingbox draw
        get_all_children = self._canvas.get_all_children
        for i in frozenset(dirty_matrix_items):
            dirty_matrix_items.update(get_all_children(i))

        # Do not update items that require a full update (or are removed)
        dirty_matrix_items = dirty_matrix_items.difference(dirty_items)

        removed_items = dirty_items.difference(self._canvas.get_all_items())
        
        try:
            for i in dirty_items:
                self.queue_draw_item(i)

            for i in dirty_matrix_items:
                try:
                    bounds = self._qtree.get_data(i)
                except KeyError:
                    dirty_items.add(i)
                else:
                    self.queue_draw_item(i)

                    self.update_matrix(i)
                    i2v = self.get_matrix_i2v(i).transform_point
                    x0, y0 = i2v(bounds.x, bounds.y)
                    x1, y1 = i2v(bounds.x1, bounds.y1)
                    vbounds = Rectangle(x0, y0, x1=x1, y1=y1)
                    self._qtree.add(i, vbounds, bounds)

                    # TODO: find an elegant way to update parent bb's.
                    parent = self.canvas.get_parent(i)
                    if parent:
                        try:
                            parent_bounds = self._qtree.get_bounds(parent)
                        except KeyError:
                            pass # No bounds, do nothing
                        else:
                            if not vbounds in parent_bounds:
                                self.set_item_bounding_box(parent, vbounds + parent_bounds)
                    self.queue_draw_item(i)

            # Remove removed items:
            dirty_items.difference_update(removed_items)
            self.selected_items.difference_update(removed_items)
            if self.focused_item in removed_items:
                self.focused_item = None
            if self.hovered_item in removed_items:
                self.hovered_item = None
            if self.dropzone_item in removed_items:
                self.dropzone_item = None

            self._update_bounding_box.update(dirty_items)

        finally:
            self._dirty_items.clear()
            self._dirty_matrix_items.clear()

    @nonrecursive
    def do_size_allocate(self, allocation):
        """
        Allocate the widget size (x, y, width, height).
        """
        gtk.DrawingArea.do_size_allocate(self, allocation)
        # doesn't work: super(GtkView, self).do_size_allocate(allocation)
        self.update_adjustments(allocation)
       
    def do_realize(self):
        #super(GtkView, self).do_realize()
        gtk.DrawingArea.do_realize(self)
        if self._canvas:
            self.request_update(self._canvas.get_all_items())

    def do_expose_event(self, event):
        """
        Render some text to the screen.
        """
        if not self._canvas:
            return

        area = event.area
        x, y, w, h = area.x, area.y, area.width, area.height
        cr = self.window.cairo_create()

        # Draw no more than nessesary.
        cr.rectangle(x, y, w, h)
        #print 'clip to', x, y, w, h
        cr.clip()

        update_bounding_box = self._update_bounding_box
        if update_bounding_box:
            try:
                cr.save()
                cr.rectangle(0, 0, 0, 0)
                cr.clip()
                try:
                    self.update_bounding_box(cr, update_bounding_box)
                finally:
                    cr.restore()
                self._idle_queue_draw_item(*update_bounding_box)
            finally:
                update_bounding_box.clear()

        self._painter.paint(Context(view=self,
                                    cairo=cr,
                                    area=Rectangle(x, y, width=w, height=h)))

        if DEBUG_DRAW_BOUNDING_BOX:
            cr.save()
            cr.identity_matrix()
            cr.set_source_rgb(0, .8, 0)
            cr.set_line_width(1.0)
            b = self._bounds
            cr.rectangle(b[0], b[1], b[2], b[3])
            cr.stroke()
            cr.restore()

        # TODO: draw Quadtree structure
        return False

    def do_event(self, event):
        """
        Handle GDK events. Events are delegated to a Tool.
        """
        handler = EVENT_HANDLERS.get(event.type)
        if self._tool and handler:
            return getattr(self._tool, handler)(ToolContext(view=self), event) and True or False
        return False

    def on_adjustment_changed(self, adj):
        """
        Change the transformation matrix of the view to reflect the
        value of the x/y adjustment (scrollbar).
        """
        if adj is self._hadjustment:
            self._matrix.translate( - self._matrix[4] / self._matrix[0] - adj.value , 0)
        elif adj is self._vadjustment:
            self._matrix.translate(0, - self._matrix[5] / self._matrix[3] - adj.value )

        # Force recalculation of the bounding boxes:
        map(self.update_matrix, self._canvas.get_all_items())
        self.request_update((), self._canvas.get_all_items())

        a = self.allocation
        super(GtkView, self).queue_draw_area(0, 0, a.width, a.height)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:
