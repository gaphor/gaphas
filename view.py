"""
This module contains everything to display a Canvas on a screen.
"""

import gtk

class View(gtk.Widget):

    def __init__(self):
        pass

    def do_expose(self, event):
        print 'expose', event

    def do_size_allocate(self, allocation):
        """allocation: a gtk.Allocation object
        """

    def do_realize(self):
        
        # create gdk.Window() for this widget.
