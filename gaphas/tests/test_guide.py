from __future__ import print_function

import unittest
from builtins import range

from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.guide import Guide, GuidedItemInMotion
from gaphas.item import Element, Line
from gaphas.view import GtkView


class GuideTestCase(unittest.TestCase):
    def setUp(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.window = Gtk.Window()
        self.window.add(self.view)
        self.window.show_all()

    def tearDown(self):
        self.window.destroy()

    def test_find_closest(self):
        """
        test find closest method.
        """
        set1 = [0, 10, 20]
        set2 = [2, 15, 30]

        guider = GuidedItemInMotion(Element(), self.view)
        d, closest = guider.find_closest(set1, set2)
        self.assertEqual(2.0, d)
        self.assertEqual([2.0], closest)

    def test_element_guide(self):
        e1 = Element()
        self.assertEqual(10, e1.width)
        self.assertEqual(10, e1.height)
        guides = Guide(e1).horizontal()
        self.assertEqual(0.0, guides[0])
        self.assertEqual(5.0, guides[1])
        self.assertEqual(10.0, guides[2])
        guides = Guide(e1).vertical()
        self.assertEqual(0.0, guides[0])
        self.assertEqual(5.0, guides[1])
        self.assertEqual(10.0, guides[2])

    def test_line_guide(self):
        c = Canvas()
        line = Line()
        c.add(line)
        line.handles().append(line._create_handle((20, 20)))
        line.handles().append(line._create_handle((30, 30)))
        line.handles().append(line._create_handle((40, 40)))
        line.orthogonal = True
        c.update_now()

        guides = list(Guide(line).horizontal())
        self.assertEqual(2, len(guides))
        self.assertEqual(10.0, guides[0])
        self.assertEqual(40.0, guides[1])

        guides = list(Guide(line).vertical())
        self.assertEqual(2, len(guides))
        self.assertEqual(00.0, guides[0])
        self.assertEqual(20.0, guides[1])

    def test_line_guide_horizontal(self):
        c = Canvas()
        line = Line()
        c.add(line)
        line.handles().append(line._create_handle((20, 20)))
        line.handles().append(line._create_handle((30, 30)))
        line.handles().append(line._create_handle((40, 40)))
        line.horizontal = True
        line.orthogonal = True
        c.update_now()

        guides = list(Guide(line).horizontal())
        self.assertEqual(2, len(guides))
        self.assertEqual(0.0, guides[0])
        self.assertEqual(20.0, guides[1])

        guides = list(Guide(line).horizontal())
        self.assertEqual(2, len(guides))
        self.assertEqual(0.0, guides[0])
        self.assertEqual(20.0, guides[1])

    def test_guide_item_in_motion(self):
        e1 = Element()
        e2 = Element()
        e3 = Element()

        canvas = self.canvas
        canvas.add(e1)
        canvas.add(e2)
        canvas.add(e3)

        self.assertEqual(0, e1.matrix[4])
        self.assertEqual(0, e1.matrix[5])

        e2.matrix.translate(40, 40)
        e2.request_update()
        self.assertEqual(40, e2.matrix[4])
        self.assertEqual(40, e2.matrix[5])

        guider = GuidedItemInMotion(e3, self.view)

        guider.start_move((0, 0))
        self.assertEqual(0, e3.matrix[4])
        self.assertEqual(0, e3.matrix[5])

        # Moved back to guided lines:
        for d in range(0, 3):
            guider.move((d, d))
            self.assertEqual(0, e3.matrix[4])
            self.assertEqual(0, e3.matrix[5])

        for d in range(3, 5):
            guider.move((d, d))
            self.assertEqual(5, e3.matrix[4])
            self.assertEqual(5, e3.matrix[5])

        guider.move((20, 20))
        self.assertEqual(20, e3.matrix[4])
        self.assertEqual(20, e3.matrix[5])

    def test_guide_item_in_motion_2(self):
        e1 = Element()
        e2 = Element()
        e3 = Element()

        canvas = self.canvas
        canvas.add(e1)
        canvas.add(e2)
        canvas.add(e3)

        self.assertEqual(0, e1.matrix[4])
        self.assertEqual(0, e1.matrix[5])

        e2.matrix.translate(40, 40)
        e2.request_update()
        self.assertEqual(40, e2.matrix[4])
        self.assertEqual(40, e2.matrix[5])

        guider = GuidedItemInMotion(e3, self.view)

        guider.start_move((3, 3))
        self.assertEqual(0, e3.matrix[4])
        self.assertEqual(0, e3.matrix[5])

        # Moved back to guided lines:
        for y in range(4, 6):
            guider.move((3, y))
            self.assertEqual(0, e3.matrix[4])
            self.assertEqual(0, e3.matrix[5])

        for y in range(6, 9):
            guider.move((3, y))
            self.assertEqual(0, e3.matrix[4])
            self.assertEqual(5, e3.matrix[5])

        # Take into account initial cursor offset of (3, 3)
        guider.move((20, 23))
        self.assertEqual(17, e3.matrix[4])
        self.assertEqual(20, e3.matrix[5])


# vim:sw=4:et:ai
