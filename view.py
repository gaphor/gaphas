"""
This module contains everything to display a Canvas on a screen.
"""

import gtk

class View(gtk.Widget):

    def __init__(self, canvas=None):
        self._canvas = canvas
        self._tool = None

    def _set_canvas(self, canvas):
        self._canvas = canvas

    canvas = property(lambda s: s._canvas, _set_canvas)

    def do_expose(self, event):
        print 'expose', event

    def do_size_allocate(self, allocation):
        """allocation: a gtk.Allocation object
        """

    def do_realize(self):
        """Realize the window (GDK) and some other stuff, used from
        the GTK+ framework.
        """
        # create gdk.Window() for this widget.

