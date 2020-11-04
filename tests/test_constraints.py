import pytest

from gaphas.constraint import (
    EqualsConstraint,
    LessThanConstraint,
    LineAlignConstraint,
    LineConstraint,
    PositionConstraint,
    constraint,
)
from gaphas.position import Position
from gaphas.solver import Variable


def test_pos_constraint():
    """Test position constraint."""
    x1, y1 = Variable(10), Variable(11)
    x2, y2 = Variable(12), Variable(13)
    pc = PositionConstraint(origin=(x1, y1), point=(x2, y2))
    pc.solve_for()

    # origin shall remain the same
    assert 10 == x1
    assert 11 == y1

    # point shall be moved to origin
    assert 10 == x2
    assert 11 == y2

    # change just x of origin
    x1.value = 15
    pc.solve_for()
    assert 15 == x2

    # change just y of origin
    y1.value = 14
    pc.solve_for()
    assert 14 == y2


def test_delta():
    """Test line align constraint delta."""
    line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
    point = (Variable(15), Variable(10))
    lc = LineAlignConstraint(line=line, point=point, align=0.5, delta=5)
    lc.solve_for()
    assert round(abs(19.16 - point[0].value), 2) == 0
    assert round(abs(12.77 - point[1].value), 2) == 0

    line[1][0].value = 40
    line[1][1].value = 30
    lc.solve_for()
    assert round(abs(24.00 - point[0].value), 2) == 0
    assert round(abs(18.00 - point[1].value), 2) == 0


def test_delta_below_zero():
    """Test line align constraint with delta below zero."""
    line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
    point = (Variable(15), Variable(10))
    lc = LineAlignConstraint(line=line, point=point, align=0.5, delta=-5)
    lc.solve_for()
    assert round(abs(10.84 - point[0].value), 2) == 0
    assert round(abs(7.23 - point[1].value), 2) == 0

    line[1][0].value = 40
    line[1][1].value = 30
    lc.solve_for()
    assert round(abs(16.0 - point[0].value), 2) == 0
    assert round(abs(12.00 - point[1].value), 2) == 0


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
