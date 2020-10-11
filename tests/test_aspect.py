"""Test aspects for items."""

import pytest

from gaphas.aspect import InMotion, Selection
from gaphas.canvas import Canvas
from gaphas.item import Item
from gaphas.view import GtkView


class CanvasViewItem:
    def __init__(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.item = Item()


@pytest.fixture()
def cvi():
    return CanvasViewItem()


def test_selection_select(cvi):
    """Test the Selection role methods."""
    cvi.canvas.add(cvi.item)
    selection = Selection(cvi.item, cvi.view)
    assert cvi.item not in cvi.view.selection.selected_items
    selection.select()
    assert cvi.item in cvi.view.selection.selected_items
    assert cvi.item is cvi.view.selection.focused_item
    selection.unselect()
    assert cvi.item not in cvi.view.selection.selected_items
    assert None is cvi.view.selection.focused_item


def test_selection_move(cvi):
    """Test the Selection role methods."""
    cvi.canvas.add(cvi.item)
    in_motion = InMotion(cvi.item, cvi.view)
    assert (1, 0, 0, 1, 0, 0) == tuple(cvi.item.matrix)
    in_motion.start_move((0, 0))
    in_motion.move((12, 26))
    assert (1, 0, 0, 1, 12, 26) == tuple(cvi.item.matrix)
