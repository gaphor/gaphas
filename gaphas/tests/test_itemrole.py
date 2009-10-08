"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.itemrole import Selection
from gaphas.canvas import Canvas, Context
from gaphas.view import View
from gaphas.tool import ToolContext

class ItemRoleTestCase(unittest.TestCase):
    """
    Test roles for items
    """

    def setUp(self):
        self.canvas = Canvas()
        self.view = View(self.canvas)
        self.context = ToolContext(view=self.view)

    def test_selection_select(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        with Selection.played_by(item):
            assert item not in view.selected_items
            item.select(self.context)
            assert item in view.selected_items
            assert item is view.focused_item
            item.unselect(self.context)
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
            item.move(Context(dx=12, dy=26))
            self.assertEquals((1, 0, 0, 1, 12, 26), tuple(item.matrix))

# vim:sw=4:et:ai
