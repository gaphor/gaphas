"""
This module contains everything to display a Canvas on a screen.
"""

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

class View(gtk.DrawingArea):
    __gtype_name__ = 'GaphasView'

    def __init__(self, canvas=None):
        super(View, self).__init__()
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.KEY_PRESS_MASK
                        | gtk.gdk.KEY_RELEASE_MASK)
        self.width = 0
        self.height = 0
        self._canvas = canvas
        self._cairo_context = None
        self._tool = None

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
                item.draw(DrawContext(view=self,
                                      cairo=cairo_context,
                                      children=self._canvas.get_children(item)))
            finally:
                cairo_context.restore()

    def do_expose_event(self, event):
        """Render some text to the screen.
        """
        # Set this to some idle function
        if self._canvas.require_update():
            self._canvas.update_now()

        viewport = self.get_allocation()
        area = event.area
        print 'expose', area.x, area.y, area.width, area.height, event.count
        if self._canvas:
            context = self.window.cairo_create()

            # Draw no more than nessesary.
            context.rectangle(area.x, area.y, area.width, area.height)
            context.clip()
            # TODO: add move/zoom matrix
            self._draw_items(self._canvas.get_root_items(), context)
        return False

    def do_button_press_event(self, event):
        print 'do button press', event
        return False

    def do_button_release_event(self, event):
        print 'do button release', event
        return False

    def do_motion_notify_event(self, event):
        print 'do motion notify', event
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

    c=Canvas()
    v.canvas = c
    b=Box()
    b.matrix=(1.0, 0.0, 0.0, 1, 20,20)
    b._width=b._height = 40
    c.add(b)
    bb=Box()
    bb.matrix=(1.0, 0.0, 0.0, 1, 10,10)
    c.add(bb, parent=b)
    bb=Box()
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)

    gtk.main()
