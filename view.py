"""
This module contains everything to display a Canvas on a screen.
"""

__version__ = "$Revision$"
# $HeadURL$

# for doctesting:
if __name__ == '__main__':
    import pygtk
    pygtk.require('2.0') 

import gobject
import gtk
from cairo import Matrix
from canvas import Context
from geometry import Rectangle
from tool import DefaultTool
from painter import DefaultPainter, BoundingBoxPainter
from decorators import async, PRIORITY_HIGH_IDLE
from decorators import nonrecursive

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False

# The default cursor (in case of a cursor reset)
DEFAULT_CURSOR = gtk.gdk.LEFT_PTR

class ToolContext(Context):
    """Special context for tools.
    """

    view = None

    def __init__(self, **kwargs):
        super(ToolContext, self).__init__(**kwargs)

    def grab(self):
        """Grab the view (or tool, depending on the implementation).
        """
        self.view.grab_focus()

    def ungrab(self):
        """Ungrab the view.
        """
        pass


class CairoContextWrapper(object):
    """Delegate all calls to the wrapped CairoContext, intercept
    stroke(), fill() and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cairo):
        self._cairo = cairo
        self._bounds = None # a Rectangle object

    def __getattr__(self, key):
        return getattr(self._cairo, key)

    def get_bounds(self):
        """Return the bounding box.
        """
        return self._bounds

    def _update_bounds(self, bounds):
        if not self._bounds:
            self._bounds = Rectangle(*bounds)
        else:
            self._bounds += bounds

    def _extents(self, extents_func, line_width=False):
        """Calculate the bounding box for a given drawing operation.
        if @line_width is True, the current line-width is taken into account.
        """
        ctx = self._cairo
        ctx.save()
        ctx.identity_matrix()
        b = getattr(ctx, extents_func)()
        ctx.restore()
        if line_width:
            # Do this after the restore(), so we can get the proper width.
            lw = self._cairo.get_line_width()/2
            d = self._cairo.user_to_device_distance(lw, lw)
            b = Rectangle(*b)
            b.expand(d[0]+d[1])
        self._update_bounds(b)
        
    def fill(self):
        self._extents('fill_extents')
        return self._cairo.fill()

    def fill_preserve(self):
        self._extents('fill_extents')
        return self._cairo.fill_preserve()

    def stroke(self):
        self._extents('stroke_extents', line_width=True)
        return self._cairo.stroke()

    def stroke_preserve(self):
        self._extents('stroke_extents', line_width=True)
        return self._cairo.stroke_preserve()

    def show_text(self, utf8):
        cairo = self._cairo
        e = cairo.text_extents(utf8)
        x0, y0 = cairo.user_to_device(e[0], e[1])
        x1, y1 = cairo.user_to_device(e[0]+e[2], e[1]+e[3])
        self._update_bounds((x0, y0, x1, y1))
        return cairo.show_text(utf8)


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


class View(gtk.DrawingArea):
    """GTK+ widget for rendering a canvas.Canvas to a screen.
    The view uses Tools from tool.py to handle events and Painters
    from painter.py to draw. Both are configurable.
    """

    # just defined a name to make GTK register this entity.
    __gtype_name__ = 'GaphasView'
    
    # Signals: emited before the change takes effect.
    __gsignals__ = {
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
        super(View, self).__init__()
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.KEY_PRESS_MASK
                        | gtk.gdk.KEY_RELEASE_MASK)
        self._canvas = canvas
        self._bounds = Rectangle()
        self._item_bounds = dict()

        # Handling selections.
        self._selected_items = set()
        self._focused_item = None
        self._hovered_item = None

        self._matrix = Matrix()

        self.hadjustment = gtk.Adjustment()
        self.vadjustment = gtk.Adjustment()

        self._tool = DefaultTool()
        self._painter = DefaultPainter()

    matrix = property(lambda s: s._matrix)

    def _set_canvas(self, canvas):
        """Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        """
        if self._canvas:
           self._canvas.unregister_view(self)

        self._canvas = canvas
        
        if self._canvas:
           self._canvas.register_view(self)
        #try:
        #    canvas._view_views.add(self)
        #except AttributeError:
        #    canvas._view_views = set([self])

    canvas = property(lambda s: s._canvas, _set_canvas)

    def select_item(self, item):
        """Select an item. This adds @item to the set of selected items. Do
           del view.selected_items
        to clear the selected items list
        
        """
        self.queue_draw_item(item, handles=True)
        if item not in self._selected_items:
            self._selected_items.add(item)
            self.emit('selection-changed', self._selected_items)

    def unselect_item(self, item):
        """Unselect an item.
        """
        self.queue_draw_item(item, handles=True)
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.emit('selection-changed', self._selected_items)

    def _del_selected_items(self):
        """Clearing the selected_item also clears the focused_item.
        """
        self.queue_draw_item(handles=True, *self._selected_items)
        self._selected_items.clear()
        self.focused_item = None
        self.emit('selection-changed', self._selected_items)

    selected_items = property(lambda s: set(s._selected_items),
                              select_item, _del_selected_items,
                              "Items selected by the view")

    def _set_focused_item(self, item):
        """Set the focused item, this item is also added to the selected_items
        set.
        """
        if not item is self._focused_item:
            self.queue_draw_item(self._focused_item, item, handles=True)

        if item:
            self.selected_items = item #.add(item)
        if item is not self._focused_item:
            self._focused_item = item
            self.emit('focus-changed', item)

    def _del_focused_item(self):
        """Items that loose focus remain selected.
        """
        self.focused_item = None
        
    focused_item = property(lambda s: s._focused_item,
                            _set_focused_item, _del_focused_item,
                            "The item with focus (receives key events a.o.)")

    def _set_hovered_item(self, item):
        """Set the hovered item.
        """
        if not item is self._hovered_item:
            self.queue_draw_item(self._hovered_item, item, handles=True)
        if item is not self._hovered_item:
            self._hovered_item = item
            self.emit('hover-changed', item)

    def _del_hovered_item(self):
        """Unset the hovered item.
        """
        self.hovered_item = None
        
    hovered_item = property(lambda s: s._hovered_item,
                            _set_hovered_item, _del_hovered_item,
                            "The item directly under the mouse pointer")

    def _set_tool(self, tool):
        """Set the tool to use. Tools should implement tool.Tool.
        """
        self._tool = tool
        self.emit('tool-changed')

    tool = property(lambda s: s._tool, _set_tool)

    def _set_painter(self, painter):
        """Set the painter to use. Painters should implement painter.Painter.
        """
        self._painter = painter
        self.emit('painter-changed')

    painter = property(lambda s: s._painter, _set_painter)

    def _set_hadjustment(self, adj):
        """Set horizontal adjustment object, for scrollbars.
        """
        #if self._hadjustment:
        #    self._hadjustment.disconnect(self.on_adjustment_changed)
        self._hadjustment = adj
        adj.connect('value_changed', self.on_adjustment_changed)

    hadjustment = property(lambda s: s._hadjustment, _set_hadjustment)

    def _set_vadjustment(self, adj):
        """Set vertical adjustment object, for scrollbars.
        """
        #if self._vadjustment:
        #    self._vadjustment.disconnect(self.on_adjustment_changed)
        self._vadjustment = adj
        adj.connect('value_changed', self.on_adjustment_changed)

    vadjustment = property(lambda s: s._vadjustment, _set_vadjustment)

    def get_item_at_point(self, x, y):
        """Return the topmost item located at (x, y).
        """
        point = (x, y)
        for item in reversed(self._canvas.get_all_items()):
            if point in self.get_item_bounding_box(item):
                inverse = Matrix(*self._matrix)
                inverse.invert()
                wx, wy = inverse.transform_point(x, y)
                ix, iy = self._canvas.get_matrix_w2i(item).transform_point(wx, wy)
                if item.point(ix, iy) < 0.5:
                    return item
        return None

    def select_in_rectangle(self, rect):
        """Select all items who have their bounding box within the
        rectangle @rect.
        """
        for item in self._canvas.get_all_items():
            if self.get_item_bounding_box(item) in rect:
                self.select_item(item)

    def zoom(self, factor):
        """Zoom in/out by factor @factor.
        """
        self._matrix.scale(factor, factor)

        # Make sure everything's updated
        self.request_update(self.canvas.get_all_items())
        a = self.allocation
        super(View, self).queue_draw_area(0, 0, a.width, a.height)

    def _update_adjustment(self, adjustment, value, canvas_size, viewport_size):
        """
        >>> v = View()
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

    def transform_distance_c2w(self, x, y):
        """Transform a point from canvas to world coordinates.
        """
        inverse = Matrix(*self._matrix)
        inverse.invert()
        return inverse.transform_distance(x, y)

    def transform_distance_w2c(self, x, y):
        """Transform a point from world to canvas coordinates.
        """
        return self._matrix.transform_distance(x, y)

    def transform_point_c2w(self, x, y):
        """Transform a point from canvas to world coordinates.
        """
        inverse = Matrix(*self._matrix)
        inverse.invert()
        return inverse.transform_point(x, y)

    def transform_point_w2c(self, x, y):
        """Transform a point from world to canvas coordinates.
        """
        return self._matrix.transform_point(x, y)

    def get_canvas_size(self):
        """The canvas size (width, height) in canvas coordinates.
        """
        inverse = Matrix(*self._matrix)
        inverse.invert()
        ww, wh = self.transform_point_c2w(self._bounds.x1, self._bounds.y1)
        return self._matrix.transform_distance(ww, wh)

    def update_adjustments(self, allocation=None):
        """Update the allocation objects (for scrollbars).
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

    def queue_draw_item(self, *items, **kwargs):
        """Like DrawingArea.queue_draw_area, but use the bounds of the
        item as update areas. Of course with a pythonic flavor: update
        any number of items at once.
        """
        handles = kwargs.get('handles')
        for item in items:
            try:
                b = self.get_item_bounding_box(item)
            except KeyError:
                pass # No bounds calculated yet? bummer.
            else:
                self.queue_draw_area(b[0]-1, b[1]-1, b[2]-b[0]+2, b[3]-b[1]+2)
                if handles:
                    for h in item.handles():
                        x, y = self._canvas.get_matrix_i2w(item).transform_point(h.x, h.y)
                        x, y = self._matrix.transform_point(x, y)
                        self.queue_draw_area(x - 5, y - 5, 10, 10)

    def queue_draw_area(self, x, y, w, h):
        """Wrap draw_area to convert all values to ints.
        """
        super(View, self).queue_draw_area(int(x), int(y), int(w+1), int(h+1))

    def set_item_bounding_box(self, item, bounds):
        """Update the bounding box of the item (in canvas coordinates).
        """
        self._item_bounds[item] = bounds
        bounds.x1 += 1
        bounds.y1 += 1
        # Also update the view's overall bounding box.
        self._bounds += bounds

    def get_item_bounding_box(self, item):
        """Get the bounding box for the item, in canvas coordinates.
        """
        return self._item_bounds[item]

    def wrap_cairo_context(self, cairo):
        """Create a wrapper class for the cairo context. This class is used
        to calculate the items bounding box while the item is drawn (the
        bounding box contains all drawn elements).
        """
        return CairoContextWrapper(cairo)

    @async(single=False, priority=PRIORITY_HIGH_IDLE)
    def request_update(self, items):
        """Update view status according to the items updated by the canvas.
        """
        if not self.window: return True

        with_handles = set(self._selected_items)
        with_handles.add(self._hovered_item)
        with_handles.add(self._focused_item)

        for i in items:
            self.queue_draw_item(i, handles=(i in with_handles))

        # Pseudo-draw
        context = self.window.cairo_create()
        context.rectangle(0,0,0,0)
        context.clip()

        self._item_bounds = dict()
        self._bounds = Rectangle()

        painter = BoundingBoxPainter()
        painter.paint(Context(view=self,
                              cairo=context))

        for i in items:
            self.queue_draw_item(i, handles=(i in with_handles))

        self.update_adjustments()

    @nonrecursive
    def do_size_allocate(self, allocation):
        """Allocate the widget size (x, y, width, height).
        """
        gtk.DrawingArea.do_size_allocate(self, allocation)
        # doesn't work: super(View, self).do_size_allocate(allocation)
        self.update_adjustments(allocation)
       
    def do_expose_event(self, event):
        """Render some text to the screen.
        """
        #print 'do_expose_event'
        if not self._canvas:
            return

        area = event.area
        self.window.draw_rectangle(self.style.white_gc, True,
                                   area.x, area.y, area.width, area.height)

        #print 'expose', area.x, area.y, area.width, area.height, event.count
        context = self.window.cairo_create()

        # Draw no more than nessesary.
        context.rectangle(area.x, area.y, area.width, area.height)
        context.clip()

        self._painter.paint(Context(view=self,
                                    cairo=context))

        if DEBUG_DRAW_BOUNDING_BOX:
            context.save()
            context.identity_matrix()
            context.set_source_rgb(0, .8, 0)
            context.set_line_width(1.0)
            b = self._bounds
            context.rectangle(b[0], b[1], b[2] - b[0], b[3] - b[1])
            context.stroke()
            context.restore()

        return False

    def do_event(self, event):
        """Handle GDK events. Events are delegated to a Tool.
        """
        handler = EVENT_HANDLERS.get(event.type)
        if self._tool and handler:
            return getattr(self._tool, handler)(ToolContext(view=self), event) and True or False
        return False

    def on_adjustment_changed(self, adj):
        """Change the transformation matrix of the view to reflect the
        value of the x/y adjustment (scrollbar).
        """
        if adj is self._hadjustment:
            self._matrix.translate( - self._matrix[4] / self._matrix[0] - adj.value , 0)
        elif adj is self._vadjustment:
            self._matrix.translate(0, - self._matrix[5] / self._matrix[3] - adj.value )

        # Force recalculation of the bounding boxes:
        self.request_update(self.canvas.get_all_items())

        a = self.allocation
        super(View, self).queue_draw_area(0, 0, a.width, a.height)


if __name__ == '__main__':
    import doctest
    doctest.testmod()


# vim: sw=4:et:
