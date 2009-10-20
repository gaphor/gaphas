"""
Test cases for the View class.
"""

import unittest
import gtk
from gaphas.view import View, GtkView
from gaphas.canvas import Canvas, Context
from gaphas.item import Line
from gaphas.examples import Box
from gaphas.tool import HoverTool


class ViewTestCase(unittest.TestCase):

    def test_bounding_box_calculations(self):
        """
        A view created before and after the canvas is populated should contain
        the same data.
        """
        canvas = Canvas()

        window1 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        view1 = GtkView(canvas=canvas)
        window1.add(view1)
        view1.realize()
        window1.show_all()

        box = Box()
        box.matrix = (1.0, 0.0, 0.0, 1, 10,10)
        canvas.add(box)

        line = Line()
        line.fyzzyness = 1
        line.handles()[1].pos = (30, 30)
        #line.split_segment(0, 3)
        line.matrix.translate(30, 60)
        canvas.add(line)

        window2 = gtk.Window(gtk.WINDOW_TOPLEVEL)
        view2 = GtkView(canvas=canvas)
        window2.add(view2)
        window2.show_all()

        # Process pending (expose) events, which cause the canvas to be drawn.
        while gtk.events_pending():
            gtk.main_iteration()

        try: 
            assert view2.get_item_bounding_box(box)
            assert view1.get_item_bounding_box(box)
            assert view1.get_item_bounding_box(box) == view2.get_item_bounding_box(box), '%s != %s' % (view1.get_item_bounding_box(box), view2.get_item_bounding_box(box))
            assert view1.get_item_bounding_box(line) == view2.get_item_bounding_box(line), '%s != %s' % (view1.get_item_bounding_box(line), view2.get_item_bounding_box(line))
        finally:
            window1.destroy()
            window2.destroy()

    def test_get_item_at_point(self):
        """
        Hover tool only reacts on motion-notify events
        """
        canvas = Canvas()
        view = GtkView(canvas)
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.add(view)
        window.show_all()

        box = Box()
        canvas.add(box)
        # No gtk main loop, so updates occur instantly
        assert not canvas.require_update()
        box.width = 50
        box.height = 50

        # Process pending (expose) events, which cause the canvas to be drawn.
        while gtk.events_pending():
            gtk.main_iteration()

        assert len(view._qtree._ids) == 1
        assert not view._qtree._bucket.bounds == (0, 0, 0, 0), view._qtree._bucket.bounds

        assert view.get_item_at_point((10, 10)) is box
        assert view.get_item_at_point((60, 10)) is None

        window.destroy()


    def test_item_removal(self):
        canvas = Canvas()
        view = GtkView(canvas)
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.add(view)
        window.show_all()

        box = Box()
        canvas.add(box)
        # No gtk main loop, so updates occur instantly
        assert not canvas.require_update()

        # Process pending (expose) events, which cause the canvas to be drawn.
        while gtk.events_pending():
            gtk.main_iteration()

        assert len(canvas.get_all_items()) == len(view._qtree)

        view.focused_item = box
        canvas.remove(box)

        assert len(canvas.get_all_items()) == 0
        assert len(view._qtree) == 0

        window.destroy()

    def test_view_registration(self):
        canvas = Canvas()

        # Simple views do not register on the canvas
        
        view = View(canvas)
        assert len(canvas._registered_views) == 0
        
        box = Box()
        canvas.add(box)

        # By default no complex updating/calculations are done:
        assert not box._matrix_i2v.has_key(view)
        assert not box._matrix_v2i.has_key(view)

        # GTK view does register for updates though

        view = GtkView(canvas)
        assert len(canvas._registered_views) == 1
        
        # No entry, since GtkView is not realized and has no window
        assert not box._matrix_i2v.has_key(view)
        assert not box._matrix_v2i.has_key(view)

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.add(view)
        window.show_all()

        # Now everything is realized and updated
        assert box._matrix_i2v.has_key(view)
        assert box._matrix_v2i.has_key(view)

        view.canvas = None
        assert len(canvas._registered_views) == 0

        assert not box._matrix_i2v.has_key(view)
        assert not box._matrix_v2i.has_key(view)

        view.canvas = canvas
        assert len(canvas._registered_views) == 1

        assert box._matrix_i2v.has_key(view)
        assert box._matrix_v2i.has_key(view)


    def test_view_registration_2(self):
        """
        Test view registration and destroy when view is destroyed.
        """
        canvas = Canvas()
        view = GtkView(canvas)
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.add(view)
        window.show_all()

        box = Box()
        canvas.add(box)

        assert hasattr(box, '_matrix_i2v')
        assert hasattr(box, '_matrix_v2i')

        assert box._matrix_i2v[view]
        assert box._matrix_v2i[view]

        assert len(canvas._registered_views) == 1
        assert view in canvas._registered_views

        window.destroy()

        assert len(canvas._registered_views) == 0

        assert not box._matrix_i2v.has_key(view)
        assert not box._matrix_v2i.has_key(view)
        

    def test_scroll_adjustments_signal(self):
        def handler(self, hadj, vadj):
            self.handled = True

        sc = gtk.ScrolledWindow()
        view = GtkView(Canvas())
        view.connect('set-scroll-adjustments', handler)
        sc.add(view)

        assert view.handled


    def test_scroll_adjustments(self):
        sc = gtk.ScrolledWindow()
        view = GtkView(Canvas())
        sc.add(view)

        print sc.get_hadjustment(), view.hadjustment
        assert sc.get_hadjustment() is view.hadjustment
        assert sc.get_vadjustment() is view.vadjustment


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
