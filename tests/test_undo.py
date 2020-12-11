from gaphas.aspect import ConnectionSink, Connector
from gaphas.canvas import Canvas
from gaphas.item import Element as Box
from gaphas.item import Line


def test_undo_on_delete_element(revert_undo, undo_fixture):
    canvas = Canvas()
    b1 = Box(canvas.connections)
    b2 = Box(canvas.connections)
    line = Line(canvas.connections)

    canvas.add(b1)
    assert 12 == len(canvas.solver.constraints)

    canvas.add(b2)
    assert 12 == len(canvas.solver.constraints)

    canvas.add(line)

    sink = ConnectionSink(b1, b1.ports()[0])
    connector = Connector(line, line.handles()[0], canvas.connections)
    connector.connect(sink)

    sink = ConnectionSink(b2, b2.ports()[0])
    connector = Connector(line, line.handles()[-1], canvas.connections)
    connector.connect(sink)

    assert 14 == len(canvas.solver.constraints)
    assert 2 == len(list(canvas.connections.get_connections(item=line)))

    del undo_fixture[2][:]  # Clear undo_list

    # Here disconnect is not invoked!
    canvas.remove(b2)

    assert 7 == len(canvas.solver.constraints)
    assert 1 == len(list(canvas.connections.get_connections(item=line)))

    cinfo = canvas.connections.get_connection(line.handles()[0])
    assert cinfo
    assert b1 == cinfo.connected

    cinfo = canvas.connections.get_connection(line.handles()[-1])
    assert cinfo is None

    undo_fixture[0]()  # Call undo

    assert 14 == len(canvas.solver.constraints)
    assert 2 == len(list(canvas.connections.get_connections(item=line)))

    cinfo = canvas.connections.get_connection(line.handles()[0])
    assert cinfo
    assert b1 == cinfo.connected

    cinfo = canvas.connections.get_connection(line.handles()[-1])
    assert cinfo
    assert b2 == cinfo.connected
