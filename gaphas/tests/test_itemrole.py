"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.itemrole import Selection
from gaphas.canvas import Canvas
from gaphas.view import View

class ItemRoleTestCase(unittest.TestCase):
    """
    Test roles for items
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
        with Selection.played_by(item):
            assert item not in view.selected_items
            item.focus(view)
            assert item in view.selected_items
            assert item is view.focused_item
            item.unselect(view)
            assert item not in view.selected_items
            assert None is view.focused_item


    def test_selection_move(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        with Selection.played_by(item):
            self.assertEquals((1, 0, 0, 1, 0, 0), tuple(item.matrix))
            item.move(12, 26)
            self.assertEquals((1, 0, 0, 1, 12, 26), tuple(item.matrix))

# vim:sw=4:et:ai
