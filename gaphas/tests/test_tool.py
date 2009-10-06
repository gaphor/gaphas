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

Event = Context

undo_list = []
redo_list = []


def undo_handler(event):
    undo_list.append(event)


def undo():
    apply_me = list(undo_list)
    del undo_list[:]
    apply_me.reverse()
    for e in apply_me:
        state.saveapply(*e)
    redo_list[:] = undo_list[:]
    del undo_list[:]


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

    self.tool = ConnectHandleTool()



class TestCaseBase(unittest.TestCase):
    """
    Abstract test case class with undo support.
    """
    def setUp(self):
        state.observers.add(state.revert_handler)
        state.subscribers.add(undo_handler)
        simple_canvas(self)

    def tearDown(self):
        state.observers.remove(state.revert_handler)
        state.subscribers.remove(undo_handler)


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
        item, port = self.tool.glue(self.view, self.line, self.head, (120, 50))
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[0], port)

        # glue to port ne-se
        item, port = self.tool.glue(self.view, self.line, self.head, (140, 70))
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[1], port)

        # glue to port se-sw
        item, port = self.tool.glue(self.view, self.line, self.head, (120, 90))
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[2], port)

        # glue to port sw-nw
        item, port = self.tool.glue(self.view, self.line, self.head, (100, 70))
        self.assertEquals(item, self.box1)
        self.assertEquals(ports[3], port)
        

    def test_failed_glue(self):
        """Test glue from too far distance"""
        item, port = self.tool.glue(self.view, self.line, self.head, (90, 50))
        self.assertTrue(item is None)
        self.assertTrue(port is None)


    def test_glue_call_can_glue_once(self):
        """Test if glue method calls can glue once only

        Box has 4 ports. Every port is examined once per
        ConnectHandleTool.glue method call. The purpose of this test is to
        assure that ConnectHandleTool.can_glue is called once (for the
        found port), it cannot be called four times (once for every port).
        """

        # count ConnectHandleTool.can_glue calls
        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0
                
            def can_glue(self, *args):
                self._calls += 1
                return True

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, (120, 50))
        assert item and port
        self.assertEquals(1, tool._calls)


    def test_glue_cannot_glue(self):
        """Test if glue method respects ConnectHandleTool.can_glue method"""

        class Tool(ConnectHandleTool):
            def can_glue(self, *args):
                return False

        tool = Tool()
        item, port = tool.glue(self.view, self.line, self.head, (120, 50))
        self.assertTrue(item is None)
        self.assertTrue(port is None)


    def test_glue_no_port_no_can_glue(self):
        """Test if glue method does not call ConnectHandleTool.can_glue method when port is not found"""

        class Tool(ConnectHandleTool):
            def __init__(self, *args):
                super(Tool, self).__init__(*args)
                self._calls = 0

            def can_glue(self, *args):
                self._calls += 1

        tool = Tool()
        # at 300, 50 there should be no item
        item, port = tool.glue(self.view, self.line, self.head, (300, 50))
        assert item is None and port is None
        self.assertEquals(0, tool._calls)



class ConnectHandleToolConnectTestCase(unittest.TestCase):

    def setUp(self):
        simple_canvas(self)


    def _get_line(self):
        line = Line()
        head = self.line.handles()[0]
        self.canvas.add(line)
        return line, head


    def test_connect(self):
        """Test connection to an item"""
        line, head = self._get_line()
        self.tool.connect(self.view, line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        self.assertTrue(cinfo is not None)
        self.assertEquals(self.box1, cinfo.connected)
        self.assertTrue(cinfo.port is self.box1.ports()[0],
            'port %s' % cinfo.port)
        self.assertTrue(isinstance(cinfo.connected, LineConstraint))
        # No default callback defined:
        self.assertTrue(cinfo.port is None)

        line, head = self._get_line()
        self.tool.connect(self.view, line, head, (90, 50))
        cinfo = self.canvas.get_connection(head)
        self.assertTrue(cinfo is None)


    def test_disconnect(self):
        """Test disconnection from an item"""
        line, head = self._get_line()
        self.tool.connect(self.view, line, head, (120, 50))

        assert line.canvas.get_connection(head) is not None


        self.tool.disconnect(self.view, line, head)
        self.assertTrue(self.canvas.get_connection(head) is None)


    def test_reconnect_another(self):
        """Test reconnection to another item"""
        line, head = self._get_line()
        self.tool.connect(self.view, line, head, (120, 50))
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
        self.tool.connect(self.view, line, head, (120, 150))
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
        self.tool.connect(self.view, line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        item = cinfo.connected
        port = cinfo.port
        constraint = cinfo.constraint

        assert item == self.box1
        assert item != self.box2

        # connect to box1 again, handle's connected item and port should be
        # the same but connection constraint will differ
        connected = self.tool.connect(self.view, line, head, (120, 50))
        cinfo = self.canvas.get_connection(head)
        assert cinfo is not None
        self.assertEqual(self.box1, cinfo.connected)
        self.assertEqual(self.box1.ports()[0], cinfo.port)
        self.assertNotEqual(constraint, cinfo.constraints)


    def test_find_port(self):
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
        def dummy_grab(): pass

        context = Context(view=self.view,
                grab=dummy_grab,
                ungrab=dummy_grab)

        head, tail = self.line.handles()

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(context, Event(x=50, y=50, state=0))
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(self.head, head)
        self.assertEquals(self.tail, tail)


    def test_merge(self):
        """Test if line is merged by moving handle onto adjacent handle
        """
        tool = LineSegmentTool()
        def dummy_grab(): pass

        context = Context(view=self.view,
                grab=dummy_grab,
                ungrab=dummy_grab)

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(context, Event(x=50, y=50, state=0))
        # start with 2 segments
        assert len(self.line.handles()) == 3

        # try to merge, now
        tool.on_button_release(context, Event(x=0, y=0, state=0))
        self.assertEquals(2, len(self.line.handles()))


    def test_merged_segment(self):
        """Test if proper segment is merged
        """
        tool = LineSegmentTool()
        def dummy_grab(): pass

        context = Context(view=self.view,
                grab=dummy_grab,
                ungrab=dummy_grab)

        self.view.hovered_item = self.line
        self.view.focused_item = self.line
        tool.on_button_press(context, Event(x=50, y=50, state=0))
        tool.on_button_press(context, Event(x=75, y=75, state=0))
        # start with 3 segments
        assert len(self.line.handles()) == 4

        # ports to be removed
        port1 = self.line.ports()[0]
        port2 = self.line.ports()[1]

        # try to merge, now
        tool.grab_handle(self.line, self.line.handles()[1])
        tool.on_button_release(context, Event(x=0, y=0, state=0))
        # check if line merging was performed
        assert len(self.line.handles()) == 3
        
        # check if proper segments were merged
        self.assertFalse(port1 in self.line.ports())
        self.assertFalse(port2 in self.line.ports())



class LineSplitTestCase(TestCaseBase):
    """
    Tests for line splitting.
    """
    def test_split_single(self):
        """Test single line splitting
        """
        # we start with two handles and one port, after split 3 handles are
        # expected and 2 ports
        assert len(self.line.handles()) == 2
        assert len(self.line.ports()) == 1

        old_port = self.line.ports()[0]
        h1, h2 = self.line.handles()
        self.assertEquals(h1.pos, old_port.start)
        self.assertEquals(h2.pos, old_port.end)

        tool = LineSegmentTool()
        
        handles, ports = tool.split_segment(self.line, 0)
        handle = handles[0]
        self.assertEquals(1, len(handles))
        self.assertEquals((50, 50), handle.pos.pos)
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(2, len(self.line.ports()))

        # new handle is between old handles
        self.assertEquals(handle, self.line.handles()[1])
        # and old port is deleted
        self.assertTrue(old_port not in self.line.ports())

        # check ports order
        p1, p2 = self.line.ports()
        h1, h2, h3 = self.line.handles()
        self.assertEquals(h1.pos, p1.start)
        self.assertEquals(h2.pos, p1.end)
        self.assertEquals(h2.pos, p2.start)
        self.assertEquals(h3.pos, p2.end)


    def test_split_multiple(self):
        """Test multiple line splitting
        """
        self.line.handles()[1].pos = (20, 16)
        handles = self.line.handles()
        old_ports = self.line.ports()[:]

        # start with two handles, split into 4 segments - 3 new handles to
        # be expected
        assert len(handles) == 2
        assert len(old_ports) == 1

        tool = LineSegmentTool()

        handles, ports = tool.split_segment(self.line, 0, count=4)
        self.assertEquals(3, len(handles))
        h1, h2, h3 = handles
        self.assertEquals((5, 4), h1.pos.pos)
        self.assertEquals((10, 8), h2.pos.pos)
        self.assertEquals((15, 12), h3.pos.pos)

        # new handles between old handles
        self.assertEquals(5, len(self.line.handles()))
        self.assertEquals(h1, self.line.handles()[1])
        self.assertEquals(h2, self.line.handles()[2])
        self.assertEquals(h3, self.line.handles()[3])

        self.assertEquals(4, len(self.line.ports()))

        # and old port is deleted
        self.assertTrue(old_ports[0] not in self.line.ports())

        # check ports order
        p1, p2, p3, p4 = self.line.ports()
        h1, h2, h3, h4, h5 = self.line.handles()
        self.assertEquals(h1.pos, p1.start)
        self.assertEquals(h2.pos, p1.end)
        self.assertEquals(h2.pos, p2.start)
        self.assertEquals(h3.pos, p2.end)
        self.assertEquals(h3.pos, p3.start)
        self.assertEquals(h4.pos, p3.end)
        self.assertEquals(h4.pos, p4.start)
        self.assertEquals(h5.pos, p4.end)


    def test_ports_after_split(self):
        """Test ports removal after split
        """
        self.line.handles()[1].pos = (20, 16)

        tool = LineSegmentTool()

        tool.split_segment(self.line, 0)
        handles = self.line.handles()
        old_ports = self.line.ports()[:]

        # start with 3 handles and two ports
        assert len(handles) == 3
        assert len(old_ports) == 2

        # do split of first segment again
        # first port should be deleted, but 2nd one should remain untouched
        tool.split_segment(self.line, 0)
        self.assertFalse(old_ports[0] in self.line.ports())
        self.assertEquals(old_ports[1], self.line.ports()[2])


    def test_constraints_after_split(self):
        """Test if constraints are recreated after line split
        """
        tool = LineSegmentTool()

        # connect line2 to self.line
        line2 = Line()
        self.canvas.add(line2)
        head = line2.handles()[0]
        self.tool.connect(self.view, line2, head, (25, 25))
        cinfo = self.canvas.get_connection(head)
        self.assertEquals(self.line, cinfo.connected)

        tool.split_segment(self.line, 0)
        assert len(self.line.handles()) == 3
        h1, h2, h3 = self.line.handles()

        # connection shall be reconstrained between 1st and 2nd handle
        self.assertEquals(h1.pos, cinfo.constraint._line[0]._point)
        self.assertEquals(h2.pos, cinfo.constraint._line[1]._point)


    def test_split_undo(self):
        """Test line splitting undo
        """
        self.line.handles()[1].pos = (20, 0)

        # we start with two handles and one port, after split 3 handles and
        # 2 ports are expected
        assert len(self.line.handles()) == 2
        assert len(self.line.ports()) == 1

        tool = LineSegmentTool()
        tool.split_segment(self.line, 0)
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2

        # after undo, 2 handles and 1 port are expected again
        undo()
        self.assertEquals(2, len(self.line.handles()))
        self.assertEquals(1, len(self.line.ports()))


    def test_orthogonal_line_split(self):
        """Test orthogonal line splitting
        """
        # start with no orthogonal constraints
        assert len(self.line._orthogonal_constraints) == 0

        self.line.orthogonal = True

        # check orthogonal constraints
        self.assertEquals(1, len(self.line._orthogonal_constraints))
        self.assertEquals(2, len(self.line.handles()))

        LineSegmentTool().split_segment(self.line, 0)

        # 3 handles and 2 ports are expected
        # 2 constraints keep the self.line orthogonal
        self.assertEquals(2, len(self.line._orthogonal_constraints))
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(2, len(self.line.ports()))


    def test_params_errors(self):
        """Test parameter error exceptions
        """
        tool = LineSegmentTool()

        # there is only 1 segment
        line = Line()
        self.assertRaises(ValueError, tool.split_segment, line, -1)

        line = Line()
        self.assertRaises(ValueError, tool.split_segment, line, 1)

        line = Line()
        # can't split into one or less segment :)
        self.assertRaises(ValueError, tool.split_segment, line, 0, 1)



class LineMergeTestCase(TestCaseBase):
    """
    Tests for line merging.
    """

    def test_merge_first_single(self):
        """Test single line merging starting from 1st segment
        """
        tool = LineSegmentTool()
        self.line.handles()[1].pos = (20, 0)
        tool.split_segment(self.line, 0)

        # we start with 3 handles and 2 ports, after merging 2 handles and
        # 1 port are expected
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2
        old_ports = self.line.ports()[:]

        handles, ports = tool.merge_segment(self.line, 0)
        # deleted handles and ports
        self.assertEquals(1, len(handles))
        self.assertEquals(2, len(ports))
        # handles and ports left after segment merging
        self.assertEquals(2, len(self.line.handles()))
        self.assertEquals(1, len(self.line.ports()))

        self.assertTrue(handles[0] not in self.line.handles())
        self.assertTrue(ports[0] not in self.line.ports())
        self.assertTrue(ports[1] not in self.line.ports())

        # old ports are completely removed as they are replaced by new one
        # port
        self.assertEquals(old_ports, ports)

        # finally, created port shall span between first and last handle
        port = self.line.ports()[0]
        self.assertEquals((0, 0), port.start.pos)
        self.assertEquals((20, 0), port.end.pos)


    def test_constraints_after_merge(self):
        """Test if constraints are recreated after line merge
        """
        tool = LineSegmentTool()
        def dummy_grab(): pass

        context = Context(view=self.view,
                grab=dummy_grab,
                ungrab=dummy_grab)

        # connect line2 to self.line
        line2 = Line()
        self.canvas.add(line2)
        head = line2.handles()[0]
        self.tool.connect(self.view, line2, head, (25, 25))
        cinfo = self.canvas.get_connection(head)
        self.assertEquals(self.line, cinfo.connected)

        tool.split_segment(self.line, 0)
        assert len(self.line.handles()) == 3
        c1 = cinfo.constraint

        tool.merge_segment(self.line, 0)
        assert len(self.line.handles()) == 2

        h1, h2 = self.line.handles()
        # connection shall be reconstrained between 1st and 2nd handle
        cinfo = self.canvas.get_connection(head)
        self.assertEquals(cinfo.constraint._line[0]._point, h1.pos)
        self.assertEquals(cinfo.constraint._line[1]._point, h2.pos)
        self.assertFalse(c1 == cinfo.constraint)


    def test_merge_multiple(self):
        """Test multiple line merge
        """
        tool = LineSegmentTool()
        self.line.handles()[1].pos = (20, 16)
        tool.split_segment(self.line, 0, count=3)
 
        # start with 4 handles and 3 ports, merge 3 segments
        assert len(self.line.handles()) == 4
        assert len(self.line.ports()) == 3
 
        print self.line.handles()
        handles, ports = tool.merge_segment(self.line, 0, count=3)
        self.assertEquals(2, len(handles))
        self.assertEquals(3, len(ports))
        self.assertEquals(2, len(self.line.handles()))
        self.assertEquals(1, len(self.line.ports()))

        self.assertTrue(not set(handles).intersection(set(self.line.handles())))
        self.assertTrue(not set(ports).intersection(set(self.line.ports())))

        # finally, created port shall span between first and last handle
        port = self.line.ports()[0]
        self.assertEquals((0, 0), port.start.pos)
        self.assertEquals((20, 16), port.end.pos)

 
    def test_merge_undo(self):
        """Test line merging undo
        """
        tool = LineSegmentTool()

        self.line.handles()[1].pos = (20, 0)

        # split for merging
        tool.split_segment(self.line, 0)
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2

        # clear undo stack before merging
        del undo_list[:]
 
        # merge with empty undo stack
        tool.merge_segment(self.line, 0)
        assert len(self.line.handles()) == 2
        assert len(self.line.ports()) == 1
 
        # after merge undo, 3 handles and 2 ports are expected again
        undo()
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(2, len(self.line.ports()))
 
 
    def test_orthogonal_line_merge(self):
        """Test orthogonal line merging
        """
        self.assertEquals(12, len(self.canvas.solver._constraints))

        tool = LineSegmentTool()
        self.line.handles()[-1].pos = 100, 100

        # prepare the self.line for merging
        tool.split_segment(self.line, 0)
        tool.split_segment(self.line, 0)
        self.line.orthogonal = True

        self.assertEquals(12 + 3, len(self.canvas.solver._constraints))
        self.assertEquals(4, len(self.line.handles()))
        self.assertEquals(3, len(self.line.ports()))

        # test the merging
        tool.merge_segment(self.line, 0)

        self.assertEquals(12 + 2, len(self.canvas.solver._constraints))
        self.assertEquals(3, len(self.line.handles()))
        self.assertEquals(2, len(self.line.ports()))

 
    def test_params_errors(self):
        """Test parameter error exceptions
        """
        tool = LineSegmentTool()

        line = Line()
        self.canvas.add(line)
        tool.split_segment(line, 0)
        # no segment -1
        self.assertRaises(ValueError, tool.merge_segment, line, -1)
 
        line = Line()
        self.canvas.add(line)
        tool.split_segment(line, 0)
        # no segment no 2
        self.assertRaises(ValueError, tool.merge_segment, line, 2)
 
        line = Line()
        self.canvas.add(line)
        tool.split_segment(line, 0)
        # can't merge one or less segments :)
        self.assertRaises(ValueError, tool.merge_segment, line, 0, 1)
 
        line = Line()
        self.canvas.add(line)
        # can't merge line with one segment
        self.assertRaises(ValueError, tool.merge_segment, line, 0)

        line = Line()
        self.canvas.add(line)
        tool.split_segment(line, 0)
        # 2 segments: no 0 and 1. cannot merge as there are no segments
        # after segment no 1
        self.assertRaises(ValueError, tool.merge_segment, line, 1)

        line = Line()
        self.canvas.add(line)
        tool.split_segment(line, 0)
        # 2 segments: no 0 and 1. cannot merge 3 segments as there are no 3
        # segments
        self.assertRaises(ValueError, tool.merge_segment, line, 0, 3)


# vim: sw=4:et:ai
