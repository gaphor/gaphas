import pytest

from gaphas.solver import BaseConstraint, MultiConstraint, Variable
from gaphas.solver.constraint import Constraint, ContainsConstraints


def test_base_constraint_implements_constraint_protocol():
    c = BaseConstraint(Variable())

    assert isinstance(c, Constraint)


def test_multi_constraint_implements_constraint_protocol():
    c = MultiConstraint()

    assert isinstance(c, Constraint)
    assert isinstance(c, ContainsConstraints)


def test_constraint_propagates_variable_changed(handler):
    v = Variable()
    c = BaseConstraint(v)
    c.add_handler(handler)

    v.value = 3

    assert handler.events == [(c,)]


def test_multi_constraint(handler):
    v = Variable()
    c = BaseConstraint(v)
    m = MultiConstraint(c)
    m.add_handler(handler)

    v.value = 3

    assert handler.events == [(c,)]


def test_default_constraint_can_not_solve():
    v = Variable()
    c = BaseConstraint(v)

    with pytest.raises(NotImplementedError):
        c.solve()


def test_constraint_handlers_are_set_just_in_time():
    v = Variable()
    c = BaseConstraint(v)

    def handler(c):
        pass

    assert not v._handlers

    c.add_handler(handler)

    assert v._handlers
    assert handler in c._handlers

    c.remove_handler(handler)

    assert not v._handlers
