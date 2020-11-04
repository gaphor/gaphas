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
from gaphas.position import Position


@pytest.fixture()
def pos1():
    return Position(1, 2)


@pytest.fixture
def pos2():
    return Position(3, 4)


def test_line_constraint(pos1):
    """Test line creation constraint."""
    line = (Position(3, 4), Position(5, 6))
    c = constraint(line=(pos1, line))

    assert isinstance(c, LineConstraint)
    assert Position(1, 2) == c._point
    assert (Position(3, 4), Position(5, 6)) == c._line


def test_horizontal_constraint(pos1, pos2):
    """Test horizontal constraint creation."""
    c = constraint(horizontal=(pos1, pos2))

    assert isinstance(c, EqualsConstraint)
    # Expect constraint on y-axis
    assert 2 == c.a
    assert 4 == c.b


def test_vertical_constraint(pos1, pos2):
    """Test vertical constraint creation."""
    c = constraint(vertical=(pos1, pos2))

    assert isinstance(c, EqualsConstraint)
    # Expect constraint on x-axis
    assert 1 == c.a
    assert 3 == c.b


def test_left_of_constraint(pos1, pos2):
    """Test "less than" constraint (horizontal) creation."""
    c = constraint(left_of=(pos1, pos2))

    assert isinstance(c, LessThanConstraint)
    assert 1 == c.smaller
    assert 3 == c.bigger


def test_above_constraint(pos1, pos2):
    """Test "less than" constraint (vertical) creation."""
    c = constraint(above=(pos1, pos2))

    assert isinstance(c, LessThanConstraint)
    assert 2 == c.smaller
    assert 4 == c.bigger
