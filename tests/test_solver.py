"""Test constraint solver."""

from gaphas.constraint import EqualsConstraint, LessThanConstraint
from gaphas.solver import REQUIRED, MultiConstraint, Solver, Variable
from gaphas.solver.constraint import Constraint, ContainsConstraints


def test_solver_implements_constraint_protocol():
    solver = Solver()

    assert isinstance(solver, Constraint)
    assert isinstance(solver, ContainsConstraints)


def test_weakest_list_order():
    solver = Solver()
    a = Variable(1, 30)
    b = Variable(2, 10)
    c_eq = EqualsConstraint(a, b)
    solver.add_constraint(c_eq)
    a.value = 4

    b.value = 5
    assert c_eq.weakest() == b

    a.value = 6
    assert c_eq.weakest() == b

    b.value = 6
    assert c_eq.weakest() == a


def test_minimal_size_constraint():
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


def test_constraints_can_not_be_resolved():
    solver = Solver()
    a = Variable()
    b = Variable()
    c = Variable(40, strength=REQUIRED)
    d = Variable(30, strength=REQUIRED)

    solver.add_constraint(EqualsConstraint(a, b))
    solver.add_constraint(EqualsConstraint(a, c))
    solver.add_constraint(EqualsConstraint(b, d))

    solver.solve()

    assert a.value == 40.0
    assert b.value == 30.0


def test_notify_for_nested_constraint():
    events = []
    solver = Solver()
    a = Variable()
    b = Variable()
    nested = EqualsConstraint(a, b)
    multi = MultiConstraint(nested)

    solver.add_constraint(multi)
    solver.solve()

    def handler(constraint):
        events.append(constraint)

    solver.add_handler(handler)

    a.value = 10

    solver.solve()

    assert multi in events
    assert nested not in events


def test_notify_for_double_nested_constraint():
    events = []
    solver = Solver()
    a = Variable()
    b = Variable()
    nested = EqualsConstraint(a, b)
    multi = MultiConstraint(nested)
    outer = MultiConstraint(multi)

    solver.add_constraint(outer)
    solver.solve()

    def handler(constraint):
        events.append(constraint)

    solver.add_handler(handler)

    a.value = 10

    solver.solve()

    assert outer in events


def test_needs_solving():
    solver = Solver()
    a = Variable()
    b = Variable()
    eq = EqualsConstraint(a, b)

    solver.add_constraint(eq)
    assert solver.needs_solving

    solver.solve()
    assert not solver.needs_solving

    a.value = 3
    assert solver.needs_solving

    solver.solve()
    assert not solver.needs_solving
