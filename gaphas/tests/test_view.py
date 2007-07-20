"""
Test cases for the View class.
"""

import unittest
import gtk
from gaphas.view import GtkView
from gaphas.canvas import Canvas, Context
from gaphas.item import Line
from gaphas.examples import Box
from gaphas.tool import ToolContext, HoverTool


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
        line.split_segment(0, 3)
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

        assert not view._update_bounding_box
        assert len(view._qtree._ids) == 1
        assert not view._qtree._bucket.bounds == (0, 0, 0, 0), view._qtree._bucket.bounds

        assert view.get_item_at_point(10, 10) is box
        assert view.get_item_at_point(60, 10) is None


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
