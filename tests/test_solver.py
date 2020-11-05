"""Test constraint solver."""
import pytest

from gaphas.constraint import EqualsConstraint, EquationConstraint, LessThanConstraint
from gaphas.solver import REQUIRED, JuggleError, Solver, Variable


def test_weakest_list_order():
    """
    Constructs a constraint order.

    Args:
    """
    solver = Solver()
    a = Variable(1, 30)
    b = Variable(2, 10)
    c = Variable(3, 10)
    c_eq = EquationConstraint(lambda a, b, c: a + b + c, a=a, b=b, c=c)
    solver.add_constraint(c_eq)
    a.value = 4

    b.value = 5
    assert c_eq.weakest() == c

    b.value = 6
    assert c_eq.weakest() == c

    # b changed above, now change a - all weakest variables changed return the
    # oldest changed variable
    c.value = 6
    assert c_eq.weakest() == b

    b.value = 6
    assert c_eq.weakest() == c


def test_minimal_size_constraint():
    """
    Test if the constraint is a constraint.

    Args:
    """
    solver = Solver()
    v1 = Variable(0)
    v2 = Variable(10)
    v3 = Variable(10)
    c1 = EqualsConstraint(a=v2, b=v3)
    c2 = LessThanConstraint(smaller=v1, bigger=v3, delta=10)
    solver.add_constraint(c1)
    solver.add_constraint(c2)

    # Check everything is ok on start
    solver.solve()
    assert 0 == v1
    assert 10 == v2
    assert 10 == v3

    # Change v1 to 2, after solve it should be 0 again due to LT constraint
    v1.value = 2
    solver.solve()

    assert 0 == v1
    assert 10 == v2
    assert 10 == v3

    # Change v3 to 20, after solve v2 will follow thanks to EQ constraint
    v3.value = 20
    solver.solve()

    assert 0 == v1
    assert 20 == v2
    assert 20 == v3

    # Change v3 to 0, after solve it should be 10 due to LT.delta = 10, v2
    # should also be 10 due to EQ constraint
    v3.value = 0
    solver.solve()

    assert 0 == v1
    assert 10 == v2
    assert 10 == v3


def test_juggle_error_is_raised_when_constraints_can_not_be_resolved():
    """
    Test if a constraint is_juggle.

    Args:
    """
    solver = Solver()
    a = Variable()
    b = Variable()
    c = Variable(40, strength=REQUIRED)
    d = Variable(30, strength=REQUIRED)

    solver.add_constraint(EqualsConstraint(a, b))
    solver.add_constraint(EqualsConstraint(a, c))
    solver.add_constraint(EqualsConstraint(b, d))

    with pytest.raises(JuggleError):
        solver.solve()
