"""Test aspects for items."""

import pytest

from gaphas.item import Element
from gaphas.move import Move


@pytest.fixture()
def item(connections):
    return Element(connections)


def test_selection_move(canvas, view, item):
    """Test the Selection role methods."""
    canvas.add(item)
    mover = Move(item, view)
    assert (1, 0, 0, 1, 0, 0) == tuple(item.matrix)
    mover.start_move((0, 0))
    mover.move((12, 26))
    assert (1, 0, 0, 1, 12, 26) == tuple(item.matrix)
