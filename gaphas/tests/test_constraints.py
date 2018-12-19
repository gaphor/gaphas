from gaphas.solver import Variable
from gaphas.constraint import PositionConstraint, LineAlignConstraint


def test_pos_constraint():
    """Test position constraint"""
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
    """Test line align constraint delta.
    """
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
    """Test line align constraint with delta below zero.
    """
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
