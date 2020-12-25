import pytest

from gaphas.canvas import Canvas
from gaphas.connections import ConnectionError
from gaphas.item import Element as Box
from gaphas.item import Line
from gaphas.matrix import Matrix
from gaphas.view.model import Model


def test_canvas_is_a_view_model(canvas):
    assert isinstance(canvas, Model)


def test_update_matrices():
    """Test updating of matrices."""
    c = Canvas()
    i = Box(c.connections)
    ii = Box(c.connections)
    c.add(i)
    c.add(ii, i)

    i.matrix().translate(5.0, 0.0)
    ii.matrix().translate(0.0, 8.0)

    assert c.get_matrix_i2c(i) == Matrix(1, 0, 0, 1, 5, 0)
    assert c.get_matrix_i2c(ii) == Matrix(1, 0, 0, 1, 5, 8)


def test_reparent():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    c.add(b1)
    c.add(b2, b1)
    c.reparent(b2, None)


def count(i):
    return len(list(i))


def test_connect_item():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    line = Line(c.connections)
    c.add(b1)
    c.add(b2)
    c.add(line)

    c.connections.connect_item(line, line.handles()[0], b1, b1.ports()[0])
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1

    # Add the same
    with pytest.raises(ConnectionError):
        c.connections.connect_item(line, line.handles()[0], b1, b1.ports()[0])
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1


def test_disconnect_item_with_callback():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    line = Line(c.connections)
    c.add(b1)
    c.add(b2)
    c.add(line)

    events = []

    def callback():
        events.append("called")

    c.connections.connect_item(
        line, line.handles()[0], b1, b1.ports()[0], callback=callback
    )
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1

    c.connections.disconnect_item(line, line.handles()[0])
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 0
    assert events == ["called"]


def test_disconnect_item_with_constraint():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    line = Line(c.connections)
    c.add(b1)
    c.add(b2)
    c.add(line)

    cons = b1.ports()[0].constraint(line, line.handles()[0], b1)

    c.connections.connect_item(
        line, line.handles()[0], b1, b1.ports()[0], constraint=cons
    )
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1

    assert len(c.solver.constraints) == 13

    c.connections.disconnect_item(line, line.handles()[0])
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 0

    assert len(c.solver.constraints) == 12


def test_disconnect_item_by_deleting_element():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    line = Line(c.connections)
    c.add(b1)
    c.add(b2)
    c.add(line)

    events = []

    def callback():
        events.append("called")

    c.connections.connect_item(
        line, line.handles()[0], b1, b1.ports()[0], callback=callback
    )
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1

    c.remove(b1)

    assert count(c.connections.get_connections(handle=line.handles()[0])) == 0
    assert events == ["called"]


def test_disconnect_item_with_constraint_by_deleting_element():
    c = Canvas()
    b1 = Box(c.connections)
    b2 = Box(c.connections)
    line = Line(c.connections)
    c.add(b1)
    c.add(b2)
    c.add(line)

    cons = b1.ports()[0].constraint(line, line.handles()[0], b1)

    c.connections.connect_item(
        line, line.handles()[0], b1, b1.ports()[0], constraint=cons
    )
    assert count(c.connections.get_connections(handle=line.handles()[0])) == 1

    ncons = len(c.solver.constraints)
    assert ncons == 13

    c.remove(b1)

    assert count(c.connections.get_connections(handle=line.handles()[0])) == 0

    assert 6 == len(c.solver.constraints)


def test_remove_connected_item():
    """Test adding canvas constraint."""
    canvas = Canvas()

    from gaphas.aspect import ConnectionSink, Connector

    l1 = Line(canvas.connections)
    canvas.add(l1)

    b1 = Box(canvas.connections)
    canvas.add(b1)

    number_cons1 = len(canvas.solver.constraints)

    b2 = Box(canvas.connections)
    canvas.add(b2)

    number_cons2 = len(canvas.solver.constraints)

    conn = Connector(l1, l1.handles()[0], canvas.connections)
    sink = ConnectionSink(b1, b1.ports()[0])

    conn.connect(sink)

    assert canvas.connections.get_connection(l1.handles()[0])

    conn = Connector(l1, l1.handles()[1], canvas.connections)
    sink = ConnectionSink(b2, b2.ports()[0])

    conn.connect(sink)

    assert canvas.connections.get_connection(l1.handles()[1])

    assert number_cons2 + 2 == len(canvas.solver.constraints)

    canvas.remove(b1)

    # Expecting a class + line connected at one end only
    assert number_cons1 + 1 == len(canvas.solver.constraints)
