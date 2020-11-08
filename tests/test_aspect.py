"""Test aspects for items."""

import pytest

from gaphas.aspect import InMotion, Selection
from gaphas.item import Element


@pytest.fixture()
def item(connections):
    return Element(connections)


def test_selection_select(canvas, view, item):
    """Test the Selection role methods."""
    canvas.add(item)
    selection = Selection(item, view)
    assert item not in view.selection.selected_items
    selection.select()
    assert item in view.selection.selected_items
    assert item is view.selection.focused_item
    selection.unselect()
    assert item not in view.selection.selected_items
    assert None is view.selection.focused_item


def test_selection_move(canvas, view, item):
    """Test the Selection role methods."""
    canvas.add(item)
    in_motion = InMotion(item, view)
    assert (1, 0, 0, 1, 0, 0) == tuple(item.matrix)
    in_motion.start_move((0, 0))
    in_motion.move((12, 26))
    assert (1, 0, 0, 1, 12, 26) == tuple(item.matrix)
