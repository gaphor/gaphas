"""Test all the tools."""
from gaphas.canvas import Context
from gaphas.tool import ConnectHandleTool

Event = Context


# Test handle connection tool glue method


def test_item_and_port_glue(simple_canvas):
    """Test glue operation to an item and its ports."""
    ports = simple_canvas.box1.ports()

    # Glue to port nw-ne
    sink = simple_canvas.tool.glue(simple_canvas.line, simple_canvas.head, (120, 50))
    assert sink.item == simple_canvas.box1
    assert ports[0] == sink.port

    # Glue to port ne-se
    sink = simple_canvas.tool.glue(simple_canvas.line, simple_canvas.head, (140, 70))
    assert sink.item == simple_canvas.box1
    assert ports[1] == sink.port

    # Glue to port se-sw
    sink = simple_canvas.tool.glue(simple_canvas.line, simple_canvas.head, (120, 90))
    assert sink.item == simple_canvas.box1
    assert ports[2] == sink.port

    # Glue to port sw-nw
    sink = simple_canvas.tool.glue(simple_canvas.line, simple_canvas.head, (100, 70))
    assert sink.item == simple_canvas.box1
    assert ports[3] == sink.port


def test_failed_glue(simple_canvas):
    """Test glue from too far distance."""
    sink = simple_canvas.tool.glue(simple_canvas.line, simple_canvas.head, (90, 50))
    assert sink is None


def test_glue_no_port_no_can_glue(simple_canvas):
    """Test no glue with no port.

    Test if glue method does not call ConnectHandleTool.can_glue method
    when port is not found.
    """

    class Tool(ConnectHandleTool):
        def __init__(self, *args):
            super().__init__(*args)
            self._calls = 0

        def can_glue(self, *args):
            self._calls += 1

    tool = Tool(simple_canvas.view)
    # At 300, 50 there should be no item
    sink = tool.glue(simple_canvas.line, simple_canvas.head, (300, 50))
    assert sink is None
    assert 0 == tool._calls


def test_connect(simple_canvas):
    """Test connection to an item."""
    line, head = simple_canvas.line, simple_canvas.head
    simple_canvas.tool.connect(line, head, (120, 50))
    cinfo = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not None
    assert simple_canvas.box1 == cinfo.connected
    assert cinfo.port is simple_canvas.box1.ports()[0], f"port {cinfo.port}"
    # No default callback defined:
    assert cinfo.callback is None

    line, head = simple_canvas.line, simple_canvas.head
    simple_canvas.tool.connect(line, head, (90, 50))
    cinfo2 = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not cinfo2, cinfo2
    assert cinfo2 is None, cinfo2


def test_reconnect_another(simple_canvas):
    """Test reconnection to another item."""
    line, head = simple_canvas.line, simple_canvas.head
    simple_canvas.tool.connect(line, head, (120, 50))
    cinfo = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not None
    item = cinfo.connected
    port = cinfo.port
    constraint = cinfo.constraint

    assert item == simple_canvas.box1
    assert port == simple_canvas.box1.ports()[0]
    assert item != simple_canvas.box2

    # Connect to box2, handle's connected item and connection data should
    # differ
    simple_canvas.tool.connect(line, head, (120, 150))
    cinfo = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not None
    assert simple_canvas.box2 == cinfo.connected
    assert simple_canvas.box2.ports()[0] == cinfo.port

    # Old connection does not exist
    assert item != cinfo.connected
    assert constraint != cinfo.constraint


def test_reconnect_same(simple_canvas):
    """Test reconnection to same item."""
    line, head = simple_canvas.line, simple_canvas.head
    simple_canvas.tool.connect(line, head, (120, 50))
    cinfo = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not None
    item = cinfo.connected
    constraint = cinfo.constraint

    assert item == simple_canvas.box1
    assert item != simple_canvas.box2

    # Connect to box1 again, handle's connected item and port should be the
    # same but connection constraint will differ
    simple_canvas.tool.connect(line, head, (120, 50))
    cinfo = simple_canvas.canvas.connections.get_connection(head)
    assert cinfo is not None
    assert simple_canvas.box1 == cinfo.connected
    assert simple_canvas.box1.ports()[0] == cinfo.port
    assert constraint != cinfo.constraint


def xtest_find_port(simple_canvas):
    """Test finding a port."""
    line, head = simple_canvas.line, simple_canvas.head
    p1, p2, p3, p4 = simple_canvas.box1.ports()

    head.pos = 110, 50
    port = simple_canvas.tool.find_port(line, head, simple_canvas.box1)
    assert p1 == port

    head.pos = 140, 60
    port = simple_canvas.tool.find_port(line, head, simple_canvas.box1)
    assert p2 == port

    head.pos = 110, 95
    port = simple_canvas.tool.find_port(line, head, simple_canvas.box1)
    assert p3 == port

    head.pos = 100, 55
    port = simple_canvas.tool.find_port(line, head, simple_canvas.box1)
    assert p4 == port
