import pytest

from gaphas.solver import Constraint, MultiConstraint, Variable


@pytest.fixture
def handler():
    """
    Decorator to register an event.

    Args:
    """
    events = []

    def handler(e):
        """
        Register an event handler.

        Args:
            e: (todo): write your description
        """
        events.append(e)

    handler.events = events  # type: ignore[attr-defined]
    return handler


def test_constraint_propagates_variable_changed(handler):
    """
    Test if variable constraints the constraint.

    Args:
        handler: (todo): write your description
    """
    v = Variable()
    c = Constraint(v)
    c.add_handler(handler)

    v.value = 3

    assert handler.events == [c]


def test_multi_constraint(handler):
    """
    Test if the constraint.

    Args:
        handler: (todo): write your description
    """
    v = Variable()
    c = Constraint(v)
    m = MultiConstraint(c)
    m.add_handler(handler)

    v.value = 3

    assert handler.events == [c]


def test_default_constraint_can_not_solve():
    """
    Whether the constraint is a constraint constraint.

    Args:
    """
    v = Variable()
    c = Constraint(v)

    with pytest.raises(NotImplementedError):
        c.solve()


def test_constraint_handlers_are_set_just_in_time():
    """
    Sets the given handlers to the given handlers.

    Args:
    """
    v = Variable()
    c = Constraint(v)

    def handler(c):
        """
        Decorator to register a handler.

        Args:
            c: (todo): write your description
        """
        pass

    assert not v._handlers

    c.add_handler(handler)

    assert v._handlers
    assert handler in c._handlers

    c.remove_handler(handler)

    assert not v._handlers
