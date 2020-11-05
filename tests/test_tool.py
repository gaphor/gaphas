"""Test all the tools."""
import pytest

from gaphas.canvas import Context
from gaphas.item import Element as Box
from gaphas.tool import ConnectHandleTool

Event = Context


@pytest.fixture
def box1(canvas, connections):
    """
    Adds a box1 box to the canvas.

    Args:
        canvas: (todo): write your description
        connections: (todo): write your description
    """
    box1 = Box(connections)
    canvas.add(box1)
    box1.matrix.translate(100, 50)
    box1.width = 40
    box1.height = 40
    canvas.request_update(box1)
    return box1


@pytest.fixture
def box2(canvas, connections):
    """
    Convert a box.

    Args:
        canvas: (todo): write your description
        connections: (todo): write your description
    """
    box2 = Box(connections)
    canvas.add(box2)
    box2.matrix.translate(100, 150)
    box2.width = 50
    box2.height = 50
    canvas.request_update(box2)
    return box2


@pytest.fixture
def tool(view):
    """
    Decorator that returns a view of the current.

    Args:
        view: (todo): write your description
    """
    return ConnectHandleTool(view)


def test_item_and_port_glue(box1, line, tool):
    """Test glue operation to an item and its ports."""
    ports = box1.ports()

    # Glue to port nw-ne
    sink = tool.glue(line, line.head, (120, 50))
    assert sink.item == box1
    assert ports[0] == sink.port

    # Glue to port ne-se
    sink = tool.glue(line, line.head, (140, 70))
    assert sink.item == box1
    assert ports[1] == sink.port

    # Glue to port se-sw
    sink = tool.glue(line, line.head, (120, 90))
    assert sink.item == box1
    assert ports[2] == sink.port

    # Glue to port sw-nw
    sink = tool.glue(line, line.head, (100, 70))
    assert sink.item == box1
    assert ports[3] == sink.port


def test_failed_glue(line, tool):
    """Test glue from too far distance."""
    sink = tool.glue(line, line.head, (90, 50))
    assert sink is None


def test_glue_no_port_no_can_glue(line, view):
    """Test no glue with no port.

    Test if glue method does not call ConnectHandleTool.can_glue method
    when port is not found.
    """

    class Tool(ConnectHandleTool):
        def __init__(self, *args):
            """
            Initialize the callable.

            Args:
                self: (todo): write your description
            """
            super().__init__(*args)
            self._calls = 0

        def can_glue(self, *args):
            """
            Takes a glue can be displayed.

            Args:
                self: (todo): write your description
            """
            self._calls += 1

    tool = Tool(view)
    # At 300, 50 there should be no item
    sink = tool.glue(line, line.head, (300, 50))
    assert sink is None
    assert 0 == tool._calls


def test_connect(connections, line, box1, tool):
    """Test connection to an item."""
    head = line.head
    tool.connect(line, head, (120, 50))
    cinfo = connections.get_connection(head)
    assert cinfo is not None
    assert box1 == cinfo.connected
    assert cinfo.port is box1.ports()[0], f"port {cinfo.port}"
    # No default callback defined:
    assert cinfo.callback is None

    tool.connect(line, head, (90, 50))
    cinfo2 = connections.get_connection(head)
    assert cinfo is not cinfo2, cinfo2
    assert cinfo2 is None, cinfo2


def test_reconnect_another(connections, line, box1, box2, tool):
    """Test reconnection to another item."""
    head = line.head
    tool.connect(line, head, (120, 50))
    cinfo = connections.get_connection(head)
    assert cinfo is not None
    item = cinfo.connected
    port = cinfo.port
    constraint = cinfo.constraint

    assert item == box1
    assert port == box1.ports()[0]
    assert item != box2

    # Connect to box2, handle's connected item and connection data should
    # differ
    tool.connect(line, head, (120, 150))
    cinfo = connections.get_connection(head)
    assert cinfo is not None
    assert box2 == cinfo.connected
    assert box2.ports()[0] == cinfo.port

    # Old connection does not exist
    assert item != cinfo.connected
    assert constraint != cinfo.constraint


def test_reconnect_same(connections, line, box1, box2, tool):
    """Test reconnection to same item."""
    head = line.head
    tool.connect(line, head, (120, 50))
    cinfo = connections.get_connection(head)
    assert cinfo is not None
    item = cinfo.connected
    constraint = cinfo.constraint

    assert item == box1
    assert item != box2

    # Connect to box1 again, handle's connected item and port should be the
    # same but connection constraint will differ
    tool.connect(line, head, (120, 50))
    cinfo = connections.get_connection(head)
    assert cinfo is not None
    assert box1 == cinfo.connected
    assert box1.ports()[0] == cinfo.port
    assert constraint != cinfo.constraint


def xtest_find_port(line, box1, tool):
    """Test finding a port."""
    head = line.head
    p1, p2, p3, p4 = box1.ports()

    head.pos = 110, 50
    port = tool.find_port(line, head, box1)
    assert p1 == port

    head.pos = 140, 60
    port = tool.find_port(line, head, box1)
    assert p2 == port

    head.pos = 110, 95
    port = tool.find_port(line, head, box1)
    assert p3 == port

    head.pos = 100, 55
    port = tool.find_port(line, head, box1)
    assert p4 == port
