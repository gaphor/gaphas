"""
Test cases for the View class.
"""

import unittest
import gtk
from gaphas.view import GtkView
from gaphas.canvas import Canvas
from gaphas.item import Line
from gaphas.examples import Box

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
        view2.realize()

        assert view2.get_item_bounding_box(box)
        assert view1.get_item_bounding_box(box)
        assert view1.get_item_bounding_box(box) == view2.get_item_bounding_box(box), '%s != %s' % (view1.get_item_bounding_box(box), view2.get_item_bounding_box(box))
        assert view1.get_item_bounding_box(line) == view2.get_item_bounding_box(line), '%s != %s' % (view1.get_item_bounding_box(line), view2.get_item_bounding_box(line))

if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
