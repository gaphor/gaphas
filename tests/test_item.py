"""Item constraint creation tests.

The test check functionality of `Item.constraint` method, not constraints
themselves.

"""
import pytest

from gaphas.constraint import LineConstraint, EqualsConstraint, LessThanConstraint
from gaphas.item import Item
from gaphas.solver import Variable


class ItemPosition:
    def __init__(self):
        self.item = Item()
        self.pos1 = Variable(1), Variable(2)
        self.pos2 = Variable(3), Variable(4)


@pytest.fixture()
def item_pos():
    return ItemPosition()


def test_line_constraint(item_pos):
    """Test line creation constraint.

    """
    line = (Variable(3), Variable(4)), (Variable(5), Variable(6))
    item_pos.item.constraint(line=(item_pos.pos1, line))
    assert 1 == len(item_pos.item._constraints)

    c = item_pos.item._constraints[0]
    assert isinstance(c, LineConstraint)
    assert (1, 2) == c._point
    assert ((3, 4), (5, 6)) == c._line


def test_horizontal_constraint(item_pos):
    """Test horizontal constraint creation.

    """
    item_pos.item.constraint(horizontal=(item_pos.pos1, item_pos.pos2))
    assert 1 == len(item_pos.item._constraints)

    c = item_pos.item._constraints[0]
    assert isinstance(c, EqualsConstraint)
    # Expect constraint on y-axis
    assert 2 == c.a
    assert 4 == c.b


def test_vertical_constraint(item_pos):
    """Test vertical constraint creation.

    """
    item_pos.item.constraint(vertical=(item_pos.pos1, item_pos.pos2))
    assert 1 == len(item_pos.item._constraints)

    c = item_pos.item._constraints[0]
    assert isinstance(c, EqualsConstraint)
    # Expect constraint on x-axis
    assert 1 == c.a
    assert 3 == c.b


def test_left_of_constraint(item_pos):
    """Test "less than" constraint (horizontal) creation.

    """
    item_pos.item.constraint(left_of=(item_pos.pos1, item_pos.pos2))
    assert 1 == len(item_pos.item._constraints)

    c = item_pos.item._constraints[0]
    assert isinstance(c, LessThanConstraint)
    assert 1 == c.smaller
    assert 3 == c.bigger


def test_above_constraint(item_pos):
    """
    Test "less than" constraint (vertical) creation.
    """
    item_pos.item.constraint(above=(item_pos.pos1, item_pos.pos2))
    assert 1 == len(item_pos.item._constraints)

    c = item_pos.item._constraints[0]
    assert isinstance(c, LessThanConstraint)
    assert 2 == c.smaller
    assert 4 == c.bigger
