import pytest

from gaphas import item
from gaphas.connections import Connections
from gaphas.constraint import EqualsConstraint
from gaphas.solver import Solver


@pytest.fixture
def connections():
    """
    Return a list of all connections.

    Args:
    """
    return Connections()


def test_connections_with_custom_solver():
    """
    Create a set of the given connections.

    Args:
    """
    solver = Solver()
    connections = Connections(solver)

    assert connections.solver is solver


def test_reconnect_item(connections):
    """
    Test for a connection isochrone.

    Args:
        connections: (todo): write your description
    """
    i = item.Line(connections)
    ii = item.Line(connections)

    cons1 = EqualsConstraint(i.handles()[0].pos.x, i.handles()[0].pos.x)
    cons2 = EqualsConstraint(i.handles()[0].pos.y, i.handles()[0].pos.y)
    connections.connect_item(i, i.handles()[0], ii, ii.ports()[0], cons1)

    assert connections.get_connection(i.handles()[0]).constraint is cons1
    assert cons1 in connections.solver.constraints

    connections.reconnect_item(i, i.handles()[0], constraint=cons2)

    assert connections.get_connection(i.handles()[0]).constraint is cons2
    assert cons1 not in connections.solver.constraints
    assert cons2 in connections.solver.constraints


def test_add_item_constraint(connections):
    """
    Add constraint constraint.

    Args:
        connections: (todo): write your description
    """
    i = item.Line(connections)
    c1 = EqualsConstraint(i.handles()[0].pos.x, i.handles()[0].pos.x)

    connections.add_constraint(i, c1)

    cinfo = next(connections.get_connections(item=i))

    assert cinfo.item is i
    assert cinfo.constraint is c1


def test_remove_item_constraint(connections):
    """
    Remove constraint from the constraint constraint.

    Args:
        connections: (todo): write your description
    """
    i = item.Line(connections)
    c1 = EqualsConstraint(i.handles()[0].pos.x, i.handles()[0].pos.x)

    connections.add_constraint(i, c1)
    connections.remove_constraint(i, c1)

    assert list(connections.get_connections(item=i)) == []


def test_remove_item_constraint_when_item_is_disconnected(connections):
    """
    Removes constraint constraint.

    Args:
        connections: (todo): write your description
    """
    i = item.Line(connections)
    c1 = EqualsConstraint(i.handles()[0].pos.x, i.handles()[0].pos.x)

    connections.add_constraint(i, c1)
    connections.disconnect_item(i)

    assert list(connections.get_connections(item=i)) == []
