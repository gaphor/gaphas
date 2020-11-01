"""Item constraint creation tests.

The test check functionality of `Item.constraint` method, not
constraints themselves.
"""
import pytest

from gaphas.constraint import (
    EqualsConstraint,
    LessThanConstraint,
    LineConstraint,
    constraint,
)
from gaphas.item import Item
from gaphas.position import Position


class ItemPosition:
    def __init__(self):
        self.item = Item()
        self.pos1 = Position((1, 2))
        self.pos2 = Position((3, 4))


@pytest.fixture()
def item_pos():
    return ItemPosition()


def test_line_constraint(item_pos):
    """Test line creation constraint."""
    line = (Position((3, 4)), Position((5, 6)))
    c = constraint(line=(item_pos.pos1, line))

    assert isinstance(c, LineConstraint)
    assert Position((1, 2)) == c._point
    assert (Position((3, 4)), Position((5, 6))) == c._line


def test_horizontal_constraint(item_pos):
    """Test horizontal constraint creation."""
    c = constraint(horizontal=(item_pos.pos1, item_pos.pos2))

    assert isinstance(c, EqualsConstraint)
    # Expect constraint on y-axis
    assert 2 == c.a
    assert 4 == c.b


def test_vertical_constraint(item_pos):
    """Test vertical constraint creation."""
    c = constraint(vertical=(item_pos.pos1, item_pos.pos2))

    assert isinstance(c, EqualsConstraint)
    # Expect constraint on x-axis
    assert 1 == c.a
    assert 3 == c.b


def test_left_of_constraint(item_pos):
    """Test "less than" constraint (horizontal) creation."""
    c = constraint(left_of=(item_pos.pos1, item_pos.pos2))

    assert isinstance(c, LessThanConstraint)
    assert 1 == c.smaller
    assert 3 == c.bigger


def test_above_constraint(item_pos):
    """Test "less than" constraint (vertical) creation."""
    c = constraint(above=(item_pos.pos1, item_pos.pos2))

    assert isinstance(c, LessThanConstraint)
    assert 2 == c.smaller
    assert 4 == c.bigger
