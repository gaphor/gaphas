"""
This module contains everything to display a Canvas on a screen.
"""

if __name__ == '__main__':
    import pygtk
    pygtk.require('2.0') 

import gtk
from cairo import Matrix, ANTIALIAS_NONE
from canvas import Context
from geometry import Rectangle

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False

class DrawContext(Context):
    """Special context for draw()'ing the item. The draw-context contains
    stuff like the view, the cairo context and properties like selected and
    focused.
    """

    def __init__(self, **kwargs):
        super(DrawContext, self).__init__(**kwargs)

    def draw_children(self):
        """Extra helper method for drawing child items from within
        the Item.draw() method.
        """
        self.view._draw_items(self.children, self.cairo)


class CairoContextWrapper(object):
    """Delegate all calls to the wrapped CairoContext, intercept
    stroke(), fill() and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cairo_context):
        self._cairo_context = cairo_context
        self._bounds = None # a Rectangle object

    def __getattr__(self, key):
        return getattr(self._cairo_context, key)

    def _update_bounds(self, bounds):
        if not self._bounds:
            self._bounds = Rectangle(*bounds)
        else:
            self._bounds += bounds

    def _extents(self, funcname):
        ctx = self._cairo_context
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(getattr(ctx, funcname)())
        ctx.restore()
        
    def fill(self):
        self._extents('fill_extents')
        return self._cairo_context.fill()

    def fill_preserve(self):
        self._extents('fill_extents')
        return self._cairo_context.fill_preserve()

    def stroke(self):
        self._extents('stroke_extents')
        return self._cairo_context.stroke()

    def stroke_preserve(self):
        self._extents('stroke_extents')
        return self._cairo_context.stroke_preserve()

    def show_text(self, utf8):
        ctx = self._cairo_context
        e = self._cairo_context.text_extents(utf8)
        x0, y0 = ctx.user_to_device(e[0], e[1])
        x1, y1 = ctx.user_to_device(e[0]+e[2], e[1]+e[3])
        self._update_bounds((x0, y0, x1, y1))
        return ctx.show_text(utf8)


# Map GDK events to tool methods
event_handlers = {
    gtk.gdk.BUTTON_PRESS: 'on_button_press',
    gtk.gdk.BUTTON_RELEASE: 'on_button_release',
    gtk.gdk._2BUTTON_PRESS: 'on_double_click',
    gtk.gdk._3BUTTON_PRESS: 'on_triple_click',
    gtk.gdk.MOTION_NOTIFY: 'on_motion_notify',
    gtk.gdk.KEY_PRESS: 'on_key_press',
    gtk.gdk.KEY_RELEASE: 'on_key_release'
}


class View(gtk.DrawingArea):
    # just defined a name to make GTK register this entity.
    __gtype_name__ = 'GaphasView'
    
    def __init__(self, canvas=None):
        super(View, self).__init__()
        self.set_flags(gtk.CAN_FOCUS)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.KEY_PRESS_MASK
                        | gtk.gdk.KEY_RELEASE_MASK)
        self._canvas = canvas

        # Handling selections.
        self._selected_items = set()
        self._focused_item = None
        self._hovered_item = None

        self._tool = None
        self._calculate_bounding_box = False

    def _set_canvas(self, canvas):
        self._canvas = canvas

    canvas = property(lambda s: s._canvas, _set_canvas)

    def select_item(self, item):
        """Select an item. This adds @item to the set of selected items. Do
           del view.selected_items
        to clear the selected items list
        
        """
        self.queue_draw_item(item, handles=True)
        self._selected_items.add(item)

    def _del_selected_items(self):
        """Clearing the selected_item also clears the focused_item.
        """
        self.queue_draw_item(handles=True, *self._selected_items)
        self._selected_items.clear()
        self._focused_item = None

    selected_items = property(lambda s: set(s._selected_items),
                              select_item, _del_selected_items,
                              "Items selected by the view")

    def _set_focused_item(self, item):
        """Set the focused item, this item is also added to the selected_items
        set.
        """
        if not item is self._focused_item:
            self.queue_draw_item(self._focused_item, item, handles=True)

        self._selected_items.add(item)
        self._focused_item = item

    def _del_focused_item(self):
        """Items that loose focus remain selected.
        """
        if self._focused_item:
            self.queue_draw_item(self._focused_item, handles=True)
        self._focused_item = None
        
    focused_item = property(lambda s: s._focused_item,
                            _set_focused_item, _del_focused_item,
                            "The item with focus (receives key events a.o.)")

    def _set_hovered_item(self, item):
        if not item is self._hovered_item:
            self.queue_draw_item(self._hovered_item, item)
        self._hovered_item = item

    def _del_hovered_item(self):
        self._hovered_item = None
        
    hovered_item = property(lambda s: s._hovered_item,
                            _set_hovered_item, _del_hovered_item,
                            "The item directly under the mouse pointer")

    def _set_tool(self, tool):
        self._tool = tool

    tool = property(lambda s: s._tool, _set_tool)

    def get_item_at_point(self, x, y):
        point = (x, y)
        for item in reversed(self._canvas.get_all_items()):
            if point in item._view_bounds:
                context = {}
                ix, iy = self._canvas.get_matrix_w2i(item).transform_point(x, y)
                if item.point(context, ix, iy) < 0.5:
                    return item
        return None

    def queue_draw_item(self, *items, **kwargs):
        """Like DrawingArea.queue_draw_area, but use the bounds of the
        item as update areas. Of course with a pythonic flavor: update
        any number of items at once.
        """
        handles = kwargs.get('handles')
        for item in items:
            try:
                b = item._view_bounds
            except AttributeError:
                pass # No bounds calculated yet? bummer.
            else:
                self.queue_draw_area(b[0], b[1], b[2] - b[0], b[3] - b[1])
		if handles:
                    for h in item.handles():
                        x, y = self._canvas.get_matrix_i2w(item).transform_point(h.x, h.y)
                        self.queue_draw_area(x - 5, y - 5, 10, 10)

    def queue_draw_area(self, x, y, w, h):
        """Wrap draw_area to convert all values to ints.
        """
        super(View, self).queue_draw_area(int(x), int(y), int(w+1), int(h+1))

#    def do_size_allocate(self, allocation):
#        super(View, self).do_size_allocate(allocation);
#        # TODO: update adjustments (v+h)
       
    def _draw_items(self, items, cairo_context):
        """Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            cairo_context.save()
            try:
                cairo_context.set_matrix(self._canvas.get_matrix_i2w(item))

                if self._calculate_bounding_box:
                    the_context = CairoContextWrapper(cairo_context)
                else:
                    # No wrapper:
                    the_context = cairo_context

                item.draw(DrawContext(view=self,
                                      cairo=the_context,
                                      parent=self._canvas.get_parent(item),
                                      children=self._canvas.get_children(item),
                                      selected=(item in self._selected_items),
                                      focused=(item is self._focused_item),
                                      hovered=(item is self._hovered_item)))

                if self._calculate_bounding_box:
                    item._view_bounds = the_context._bounds
                    item._view_bounds.x1 += 1
                    item._view_bounds.y1 += 1

                if DEBUG_DRAW_BOUNDING_BOX:
                    ctx = cairo_context
                    ctx.save()
                    ctx.identity_matrix()
                    ctx.set_source_rgb(.8, 0, 0)
                    ctx.set_line_width(1.0)
                    b = item._view_bounds
                    ctx.rectangle(b[0], b[1], b[2] - b[0], b[3] - b[1])
                    ctx.stroke()
                    ctx.restore()
            finally:
                cairo_context.restore()

    def _draw_handles(self, item, cairo_context):
        """Draw handles for an item.
        The handles are drawn in non-antialiased mode for clearity.
        """
        cairo_context.save()
        cairo_context.identity_matrix()
        m = self._canvas.get_matrix_i2w(item)
        opacity = (item is self._focused_item) and .7 or .4
        for h in item.handles():
            cairo_context.save()
            cairo_context.set_antialias(ANTIALIAS_NONE)
            cairo_context.translate(*m.transform_point(h.x, h.y))
            cairo_context.rectangle(-4, -4, 8, 8)
            cairo_context.set_source_rgba(0, 1, 0, opacity)
            cairo_context.fill_preserve()
            cairo_context.move_to(-2, -2)
            cairo_context.line_to(2, 3)
            cairo_context.move_to(2, -2)
            cairo_context.line_to(-2, 3)
            cairo_context.set_source_rgba(0, .2, 0, 0.9)
            cairo_context.set_line_width(1)
            cairo_context.stroke()
            cairo_context.restore()
        cairo_context.restore()

    def do_expose_event(self, event):
        """Render some text to the screen.
        """
        # Set this to some idle function
        if self._canvas.require_update():
            self._canvas.update_now()
            self._calculate_bounding_box = True

        viewport = self.get_allocation()
        area = event.area
        self.window.draw_rectangle(self.style.white_gc, True,
                                   area.x, area.y, area.width, area.height)

        #print 'expose', area.x, area.y, area.width, area.height, event.count
        if self._canvas:
            context = self.window.cairo_create()

            # Draw no more than nessesary.
            context.rectangle(area.x, area.y, area.width, area.height)
            context.clip()
            # TODO: add move/zoom matrix

            self._draw_items(self._canvas.get_root_items(), context)

            # Draw handles of selected items on top of the items.
            # Conpare with canvas.get_all_items() to determine drawing order.
            for item in (i for i in self._canvas.get_all_items() if i in self._selected_items):
                self._draw_handles(item, context)

            if self._tool:
                self._tool.draw(Context(view=self, cairo=context))

        self._calculate_bounding_box = False

        return False

    def do_event(self, event):
        """Handle GDK events. Events are delegated to a Tool.
        """
        handler = event_handlers.get(event.type)
        if self._tool and handler:
            return getattr(self._tool, handler)(self, event) and True or False
        return False

if __name__ == '__main__':
    from canvas import Canvas
    from examples import Box, Text
    from tool import DefaultToolChain
    import math
    w = gtk.Window()
    v = View()
    w.add(v)
    w.connect('destroy', gtk.main_quit)
    w.show_all()

    c=Canvas()
    v.canvas = c
    v.tool = DefaultToolChain()
#    v.tool = HandleTool()
    b=Box()
    print 'box', b
    b.matrix=(1.0, 0.0, 0.0, 1, 20,20)
    b.width=b.height = 40
    c.add(b)
    bb=Box()
    print 'box', bb
    bb.matrix=(1.0, 0.0, 0.0, 1, 10,10)
    c.add(bb, parent=b)
    #v.selected_items = bb
    bb=Box()
    print 'box', bb
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)
    t=Text()
    t.matrix.translate(70,70)
    c.add(t)
    gtk.main()


# vim: sw=4:et:
