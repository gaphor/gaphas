"""
Test all the tools provided by gaphas.
"""

import unittest

from gaphas.tool import ConnectHandleTool, LineSegmentTool
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Item, Element, Line
from gaphas.view import View, GtkView
from gaphas.constraint import LineConstraint
from gaphas.canvas import Context
from gaphas import state

from gaphas.aspect import Segment, Connector, ConnectionSink


Event = Context


def simple_canvas(self):
    """
    This decorator adds view, canvas and handle connection tool to a test
    case. Two boxes and a line are added to the canvas as well.
    """
    self.canvas = Canvas()

    self.box1 = Box()
    self.canvas.add(self.box1)
    self.box1.matrix.translate(100, 50)
    self.box1.width = 40 
    self.box1.height = 40 
    self.box1.request_update()

    self.box2 = Box()
    self.canvas.add(self.box2)
    self.box2.matrix.translate(100, 150)
    self.box2.width = 50 
    self.box2.height = 50 
    self.box2.request_update()

    self.line = Line()
    self.head = self.line.handles()[0]
    self.tail = self.line.handles()[-1]
    self.tail.pos = 100, 100
    self.canvas.add(self.line)

    self.canvas.update_now()
    self.view = GtkView()
    self.view.canvas = self.canvas
    import gtk
    win = gtk.Window()
    win.add(self.view)
    self.view.show()
    self.view.update()
    win.show()

    self.tool = ConnectHandleTool(self.view)



class ConnectHandleToolGlueTestCase(unittest.TestCase):
    """
    Test handle connection tool glue method.
    """

    def setUp(self):
        simple_canvas(self)


    def test_item_and_port_glue(self):
        """Test glue operation to an item and its ports"""

        ports = self.box1.ports()

        # glue to port nw-ne
        sink = self.tool.glue(self.line, self.head, (120, 50))
        self.assertEquals(sink.item, self.box1)
        self.assertEquals(ports[0], sink.port)

        # glue to port ne-se
        sink = self.tool.glue(self.line, self.head, (140, 70))
        self.assertEquals(sink.item, self.box1)
        self.assertEquals(ports[1], sink.port)

        # glue to port se-sw
        sink = self.tool.glue(self.line, self.head, (120, 90))
        self.assertEquals(sink.item, self.box1)
        self.assertEquals(ports[2], sink.port)

        # glue to port sw-nw
        sink = self.tool.glue(self.line, self.head, (100, 70))
        self.assertEquals(sink.item, self.box1)
        self.assertEquals(ports[3], sink.port)
        

    def test_failed_glue(self):
        """Test glue from too far distance"""
        sink = self.tool.glue(self.line, self.head, (90, 50))
        self.assertTrue(sink is None)


#    def test_glue_call_can_glue_once(self):
#        """Test if glue method calls can glue once only
#
#        Box has 4 ports. Every port is examined once per
#        ConnectHandleTool.glue method call. The purpose of this test is to
#        assure that ConnectHandleTool.can_glue is called once (for the
#        found port), it cannot be called four times (once for every port).
#        """
#
#        # count ConnectHandleTool.can_glue calls
#        class Tool(ConnectHandleTool):
#            def __init__(self, *args):
#                super(Tool, self).__init__(*args)
#                self._calls = 0
#                
#            def can_glue(self, *args):
#                self._calls += 1
#                return True
#
#        tool = Tool(self.view)
#        item, port = tool.glue(self.line, self.head, (120, 50))
#        assert item and port
#        self.assertEquals(1, tool._calls)


#    def test_glue_cannot_glue(self):
#        """Test if glue method respects ConnectHandleTool.can_glue method"""
#
#        class Tool(ConnectHandleTool):
#            def can_glue(self, *args):
#                return False
#
#        tool = Tool(self.view)
#        item, port = tool.glue(self.line, self.head, (120, 50))
#        self.assertTrue(item is None, item)
#        self.assertTrue(port is None, port)


    def test_glue_no_port_no_can_glue(self):
        """Test if glue method does not call ConnectHandleTool.can_glue method when port is not found"""

        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0

            def can_glue(self, *args):
                self._calls += 1

        tool = Tool(self.view)
        # at 300, 50 there should be no item
        sink = tool.glue(self.line, self.head, (300, 50))
        assert sink is None
        self.assertEquals(0, tool._calls)



class ConnectHandleToolConnectTestCase(unittest.TestCase):

    def setUp(self):
        simple_canvas(self)


    def _get_line(self):
        line = Line()
        head = line.handles()[0]
        self.canvas.add(line)
        return line, head


    def test_connect(self):
        """Test connection to an item"""
        line, head = self._get_line()
        self.tool.connect(line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        self.assertTrue(cinfo is not None)
        self.assertEquals(self.box1, cinfo.connected)
        self.assertTrue(cinfo.port is self.box1.ports()[0],
            'port %s' % cinfo.port)
        self.assertTrue(isinstance(cinfo.constraint, LineConstraint))
        # No default callback defined:
        self.assertTrue(cinfo.callback is None)

        line, head = self._get_line()
        self.tool.connect(line, head, (90, 50))
        cinfo2 = self.canvas.get_connection(head)
        self.assertTrue(cinfo is not cinfo2, cinfo2)
        self.assertTrue(cinfo2 is None, cinfo2)


    def test_disconnect(self):
        """Test disconnection from an item"""
        line, head = self._get_line()
        self.tool.connect(line, head, (120, 50))

        assert line.canvas.get_connection(head) is not None


        self.tool.disconnect(line, head)
        self.assertTrue(self.canvas.get_connection(head) is None)


    def test_reconnect_another(self):
        """Test reconnection to another item"""
        line, head = self._get_line()
        self.tool.connect(line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        item = cinfo.connected
        port = cinfo.port
        constraint = cinfo.constraint

        assert item == self.box1
        assert port == self.box1.ports()[0]
        assert item != self.box2

        # connect to box2, handle's connected item and connection data
        # should differ
        self.tool.connect(line, head, (120, 150))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        self.assertEqual(self.box2, cinfo.connected)
        self.assertEqual(self.box2.ports()[0], cinfo.port)

        # old connection does not exist
        self.assertNotEqual(item, cinfo.connected)
        self.assertNotEqual(constraint, cinfo.constraint)


    def test_reconnect_same(self):
        """Test reconnection to same item"""
        line, head = self._get_line()
        self.tool.connect(line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        item = cinfo.connected
        port = cinfo.port
        constraint = cinfo.constraint

        assert item == self.box1
        assert item != self.box2

        # connect to box1 again, handle's connected item and port should be
        # the same but connection constraint will differ
        connected = self.tool.connect(line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        self.assertEqual(self.box1, cinfo.connected)
        self.assertEqual(self.box1.ports()[0], cinfo.port)
        self.assertNotEqual(constraint, cinfo.constraint)


    def xtest_find_port(self):
        """Test finding a port
        """
        line, head = self._get_line()
        p1, p2, p3, p4 = self.box1.ports()

        head.pos = 110, 50
        port = self.tool.find_port(line, head, self.box1)
        self.assertEquals(p1, port)

        head.pos = 140, 60
        port = self.tool.find_port(line, head, self.box1)
        self.assertEquals(p2, port)

        head.pos = 110, 95
        port = self.tool.find_port(line, head, self.box1)
        self.assertEquals(p3, port)

        head.pos = 100, 55
        port = self.tool.find_port(line, head, self.box1)
        self.assertEquals(p4, port)



class LineSegmentToolTestCase(unittest.TestCase):
    """
    Line segment tool tests.
    """
    def setUp(self):
        simple_canvas(self)

    def test_split(self):
        """Test if line is splitted while pressing it in the middle
        """
        tool = LineSegmentTool()
        tool.set_view(self.view)

        head, tail = self.line.handles()

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(Event(x=50, y=50, state=0))
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(self.head, head)
        self.assertEquals(self.tail, tail)


    def test_merge(self):
        """Test if line is merged by moving handle onto adjacent handle
        """
        tool = LineSegmentTool()
        tool.set_view(self.view)
        def dummy_grab(): pass

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(Event(x=50, y=50, state=0))
        # start with 2 segments
        assert len(self.line.handles()) == 3

        # try to merge, now
        tool.on_button_release(Event(x=0, y=0, state=0))
        self.assertEquals(2, len(self.line.handles()))


    def test_merged_segment(self):
        """Test if proper segment is merged
        """
        tool = LineSegmentTool()
        tool.set_view(self.view)

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(Event(x=50, y=50, state=0))
        tool.on_button_press(Event(x=75, y=75, state=0))
        # start with 3 segments
        assert len(self.line.handles()) == 4
        assert len(self.line.ports()) == 3

        # ports to be removed
        port1 = self.line.ports()[0]
        port2 = self.line.ports()[1]

        # try to merge, now
        tool.handle_tool.grab_handle(self.line, self.line.handles()[1])
        tool.on_button_release(Event(x=0, y=0, state=0))
        # check if line merging was performed
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2
        
        # check if proper segments were merged
        #self.assertFalse(port1 in self.line.ports(), "%s (%s)" % (port1, self.line.ports()))
        self.assertFalse(port2 in self.line.ports())

        handles = self.line.handles()
        self.assertTrue(port1.start is handles[0].pos)
        self.assertTrue(port1.end is handles[1].pos)

        ports = self.line.ports()
        self.assertTrue(ports[0].start is handles[0].pos)
        self.assertTrue(ports[0].end is handles[1].pos)
        self.assertTrue(ports[1].start is handles[1].pos)
        self.assertTrue(ports[1].end is handles[2].pos)


# vim: sw=4:et:ai
