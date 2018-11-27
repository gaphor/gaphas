"""
Generic gaphas item tests.
"""

import unittest

from gaphas.aspect import *
from gaphas.canvas import Canvas
from gaphas.view import View


class AspectTestCase(unittest.TestCase):
    """
    Test aspects for items.
    """

    def setUp(self):
        self.canvas = Canvas()
        self.view = View(self.canvas)

    def test_selection_select(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        selection = Selection(item, view)
        assert item not in view.selected_items
        selection.select()
        assert item in view.selected_items
        assert item is view.focused_item
        selection.unselect()
        assert item not in view.selected_items
        assert None is view.focused_item

    def test_selection_move(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        inmotion = InMotion(item, view)
        self.assertEqual((1, 0, 0, 1, 0, 0), tuple(item.matrix))
        inmotion.start_move((0, 0))
        inmotion.move((12, 26))
        self.assertEqual((1, 0, 0, 1, 12, 26), tuple(item.matrix))


# vim:sw=4:et:ai
