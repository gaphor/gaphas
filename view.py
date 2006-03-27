"""
This module contains everything to display a Canvas on a screen.
"""

if __name__ == '__main__':
    import pygtk
    pygtk.require('2.0') 

import gtk
from cairo import Matrix
from canvas import Context

class DrawContext(Context):

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
        self._bounds = None

    def __getattr__(self, key):
        return getattr(self._cairo_context, key)

    def _update_bounds(self, bounds):
        #print 'bounds', bounds
        if not self._bounds:
            self._bounds = bounds
        else:
            b = self._bounds
            self._bounds = (min(b[0], bounds[0]), min(b[1], bounds[1]),
                            max(b[2], bounds[2]), max(b[3], bounds[3]))

    def fill(self):
        ctx = self._cairo_context
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(ctx.fill_extents())
        ctx.restore()
        return ctx.fill()

    def fill_preserve(self):
        ctx = self._cairo_context
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(ctx.fill_extents())
        ctx.restore()
        return ctx.fill_preserve()

    def stroke(self):
        ctx = self._cairo_context
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(ctx.stroke_extents())
        ctx.restore()
        return ctx.stroke()

    def stroke_preserve(self):
        ctx = self._cairo_context
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(ctx.stroke_extents())
        ctx.restore()
        return ctx.stroke_preserve()

    def text_show(self, utf8):
        e = self._cairo_context.text_extents(utf8)
        # Do something with it
        return ctx.show_text(utf8)


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
        self._cairo_context = None
        self._tool = None
        self._calculate_bounding_box = False

        # Handy debug flag for drawing bounding boxes around the items.
        self._debug_draw_bounding_box = True

    def _set_canvas(self, canvas):
        self._canvas = canvas

    canvas = property(lambda s: s._canvas, _set_canvas)

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
                cairo_context.set_matrix(item._matrix_w2i)
                #cairo_context.transform(Matrix(*item.matrix))

                if self._calculate_bounding_box:
                    wrapper = CairoContextWrapper(cairo_context)
                else:
                    # No wrapper:
                    wrapper = cairo_context

                item.draw(DrawContext(view=self,
                                      cairo=wrapper,
                                      children=self._canvas.get_children(item)))

                if self._calculate_bounding_box:
                    item._view_bounds = wrapper._bounds
                    #print item, wrapper._bounds

                if self._debug_draw_bounding_box:
                    ctx = cairo_context
                    ctx.save()
                    ctx.identity_matrix()
                    ctx.set_source_rgb(.8, 0, 0)
                    ctx.set_line_width(1.0)
                    b = item._view_bounds
                    ctx.rectangle(b[0], b[1], b[2] - b[0], b[3] - b[1])
                    ctx.stroke()
                    ctx.restore()

                self._draw_handles(item, cairo_context)
            finally:
                cairo_context.restore()

    def _draw_handles(self, item, cairo_context):
        for handle in item.handles():
            cairo_context.save()
            cairo_context.translate(handle.x - 4, handle.y - 4)
            cairo_context.rectangle(0, 0, 9, 9)
            cairo_context.set_source_rgba(0, 1, 0, .6)
            cairo_context.fill_preserve()
            cairo_context.move_to(2, 2)
            cairo_context.line_to(7, 7)
            cairo_context.move_to(7, 2)
            cairo_context.line_to(2, 7)
            cairo_context.set_source_rgba(0, .2, 0, 0.9)
            cairo_context.set_line_width(1.1)
            cairo_context.stroke()
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
        self.window.draw_rectangle(self.style.white_gc, True, area.x, area.y, area.width, area.height)

        print 'expose', area.x, area.y, area.width, area.height, event.count
        if self._canvas:
            context = self.window.cairo_create()

            # Draw no more than nessesary.
            context.rectangle(area.x, area.y, area.width, area.height)
            context.clip()
            # TODO: add move/zoom matrix
            self._draw_items(self._canvas.get_root_items(), context)

        self._calculate_bounding_box = False

        return False

    def do_button_press_event(self, event):
        print 'do button press', event
        return False

    def do_button_release_event(self, event):
        print 'do button release', event
        return False

    def do_motion_notify_event(self, event):
        #print 'do motion notify', event
        return False

    def do_key_press_event(self, event):
        print 'do key press', event
        return False

    def do_key_release_event(self, event):
        print 'do key release', event
        return False

if __name__ == '__main__':
    from canvas import Canvas
    from examples import Box
    import math
    w = gtk.Window()
    v = View()
    w.add(v)
    w.connect('destroy', gtk.main_quit)
    w.show_all()

    gtk.rc_parse_string("""
    style "background" { bg[NORMAL] = "white" fg[NORMAL] = "white" }
    class "GaphasView" style "background"
    """)
    c=Canvas()
    v.canvas = c
    print 'view', v
    b=Box()
    print 'box', b
    b.matrix=(1.0, 0.0, 0.0, 1, 20,20)
    b._width=b._height = 40
    c.add(b)
    bb=Box()
    print 'box', bb
    bb.matrix=(1.0, 0.0, 0.0, 1, 10,10)
    c.add(bb, parent=b)
    bb=Box()
    print 'box', bb
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)

    gtk.main()
