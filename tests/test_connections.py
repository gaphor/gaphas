import pytest

from gaphas import item
from gaphas.connections import Connections
from gaphas.constraint import EqualsConstraint
from gaphas.solver import Solver


@pytest.fixture
def connections():
    return Connections(Solver())


def test_reconnect_item(connections):
    i = item.Line()
    ii = item.Line()

    cons1 = EqualsConstraint(i.handles()[0].pos.x, i.handles()[0].pos.x)
    cons2 = EqualsConstraint(i.handles()[0].pos.y, i.handles()[0].pos.y)
    connections.connect_item(i, i.handles()[0], ii, ii.ports()[0], cons1)

    assert connections.get_connection(i.handles()[0]).constraint is cons1
    assert cons1 in connections.solver.constraints

    connections.reconnect_item(i, i.handles()[0], constraint=cons2)

    assert connections.get_connection(i.handles()[0]).constraint is cons2
    assert cons1 not in connections.solver.constraints
    assert cons2 in connections.solver.constraints
