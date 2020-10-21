import pytest

from gaphas.solver import Constraint, MultiConstraint, Variable


@pytest.fixture
def handler():
    events = []

    def handler(e):
        events.append(e)

    handler.events = events  # type: ignore[attr-defined]
    return handler


def test_constraint_propagates_variable_changed(handler):
    v = Variable()
    c = Constraint(v)
    c.add_handler(handler)

    v.value = 3

    assert handler.events == [c]


def test_multi_constraint(handler):
    v = Variable()
    c = Constraint(v)
    m = MultiConstraint(c)
    m.add_handler(handler)

    v.value = 3

    assert handler.events == [c]


def test_default_constraint_can_not_solve():
    v = Variable()
    c = Constraint(v)

    with pytest.raises(NotImplementedError):
        c.solve()
