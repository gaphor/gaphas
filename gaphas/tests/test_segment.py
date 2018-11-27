"""
Generic gaphas item tests.
"""
from __future__ import print_function

import unittest

from gaphas.item import Item, Line
from gaphas.segment import *
from gaphas.canvas import Canvas
from gaphas.view import View
from gaphas import state
from gaphas.tests.test_tool import simple_canvas


class SegmentTestCase(unittest.TestCase):
    """
    Test aspects for items.
    """

    def setUp(self):
        self.canvas = Canvas()
        self.line = Line()
        self.view = View(self.canvas)

    def test_segment_fails_for_item(self):
        """
        Test if Segment aspect can be applied to Item
        """
        item = Item()
        try:
            s = Segment(item, self.view)
        except TypeError as e:
            pass
        else:
            assert False, "Should not be reached"

    def test_segment(self):
        """
        """
        view = self.view
        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        self.assertEqual(2, len(line.handles()))
        segment.split((5, 5))
        self.assertEqual(3, len(line.handles()))


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
        self.assertEqual(h1.pos, old_port.start)
        self.assertEqual(h2.pos, old_port.end)

        segment = Segment(self.line, self.view)

        handles, ports = segment.split_segment(0)
        handle = handles[0]
        self.assertEqual(1, len(handles))
        self.assertEqual((50, 50), handle.pos.pos)
        self.assertEqual(3, len(self.line.handles()))
        self.assertEqual(2, len(self.line.ports()))

        # new handle is between old handles
        self.assertEqual(handle, self.line.handles()[1])
        # and old port is deleted
        self.assertTrue(old_port not in self.line.ports())

        # check ports order
        p1, p2 = self.line.ports()
        h1, h2, h3 = self.line.handles()
        self.assertEqual(h1.pos, p1.start)
        self.assertEqual(h2.pos, p1.end)
        self.assertEqual(h2.pos, p2.start)
        self.assertEqual(h3.pos, p2.end)

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

        segment = Segment(self.line, self.view)

        handles, ports = segment.split_segment(0, count=4)
        self.assertEqual(3, len(handles))
        h1, h2, h3 = handles
        self.assertEqual((5, 4), h1.pos.pos)
        self.assertEqual((10, 8), h2.pos.pos)
        self.assertEqual((15, 12), h3.pos.pos)

        # new handles between old handles
        self.assertEqual(5, len(self.line.handles()))
        self.assertEqual(h1, self.line.handles()[1])
        self.assertEqual(h2, self.line.handles()[2])
        self.assertEqual(h3, self.line.handles()[3])

        self.assertEqual(4, len(self.line.ports()))

        # and old port is deleted
        self.assertTrue(old_ports[0] not in self.line.ports())

        # check ports order
        p1, p2, p3, p4 = self.line.ports()
        h1, h2, h3, h4, h5 = self.line.handles()
        self.assertEqual(h1.pos, p1.start)
        self.assertEqual(h2.pos, p1.end)
        self.assertEqual(h2.pos, p2.start)
        self.assertEqual(h3.pos, p2.end)
        self.assertEqual(h3.pos, p3.start)
        self.assertEqual(h4.pos, p3.end)
        self.assertEqual(h4.pos, p4.start)
        self.assertEqual(h5.pos, p4.end)

    def test_ports_after_split(self):
        """Test ports removal after split
        """
        self.line.handles()[1].pos = (20, 16)

        segment = Segment(self.line, self.view)

        segment.split_segment(0)
        handles = self.line.handles()
        old_ports = self.line.ports()[:]

        # start with 3 handles and two ports
        assert len(handles) == 3
        assert len(old_ports) == 2

        # do split of first segment again
        # first port should be deleted, but 2nd one should remain untouched
        segment.split_segment(0)
        self.assertFalse(old_ports[0] in self.line.ports())
        self.assertEqual(old_ports[1], self.line.ports()[2])

    def test_constraints_after_split(self):
        """Test if constraints are recreated after line split
        """

        # connect line2 to self.line
        line2 = Line()
        self.canvas.add(line2)
        head = line2.handles()[0]
        self.tool.connect(line2, head, (25, 25))
        cinfo = self.canvas.get_connection(head)
        self.assertEqual(self.line, cinfo.connected)

        Segment(self.line, self.view).split_segment(0)
        assert len(self.line.handles()) == 3
        h1, h2, h3 = self.line.handles()

        cinfo = self.canvas.get_connection(head)
        # connection shall be reconstrained between 1st and 2nd handle
        self.assertEqual(h1.pos, cinfo.constraint._line[0]._point)
        self.assertEqual(h2.pos, cinfo.constraint._line[1]._point)

    def test_split_undo(self):
        """Test line splitting undo
        """
        self.line.handles()[1].pos = (20, 0)

        # we start with two handles and one port, after split 3 handles and
        # 2 ports are expected
        assert len(self.line.handles()) == 2
        assert len(self.line.ports()) == 1

        segment = Segment(self.line, self.view)
        segment.split_segment(0)
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2

        # after undo, 2 handles and 1 port are expected again
        undo()
        self.assertEqual(2, len(self.line.handles()))
        self.assertEqual(1, len(self.line.ports()))

    def test_orthogonal_line_split(self):
        """Test orthogonal line splitting
        """
        # start with no orthogonal constraints
        assert len(self.line._orthogonal_constraints) == 0

        segment = Segment(self.line, None)
        segment.split_segment(0)

        self.line.orthogonal = True

        # check orthogonal constraints
        self.assertEqual(2, len(self.line._orthogonal_constraints))
        self.assertEqual(3, len(self.line.handles()))

        Segment(self.line, self.view).split_segment(0)

        # 3 handles and 2 ports are expected
        # 2 constraints keep the self.line orthogonal
        self.assertEqual(3, len(self.line._orthogonal_constraints))
        self.assertEqual(4, len(self.line.handles()))
        self.assertEqual(3, len(self.line.ports()))

    def test_params_errors(self):
        """Test parameter error exceptions
        """
        line = Line()
        segment = Segment(line, self.view)

        # there is only 1 segment
        self.assertRaises(ValueError, segment.split_segment, -1)

        line = Line()
        segment = Segment(line, self.view)
        self.assertRaises(ValueError, segment.split_segment, 1)

        line = Line()
        # can't split into one or less segment :)
        segment = Segment(line, self.view)
        self.assertRaises(ValueError, segment.split_segment, 0, 1)


class LineMergeTestCase(TestCaseBase):
    """
    Tests for line merging.
    """

    def test_merge_first_single(self):
        """Test single line merging starting from 1st segment
        """
        self.line.handles()[1].pos = (20, 0)
        segment = Segment(self.line, self.view)
        segment.split_segment(0)

        # we start with 3 handles and 2 ports, after merging 2 handles and
        # 1 port are expected
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2
        old_ports = self.line.ports()[:]

        segment = Segment(self.line, self.view)
        handles, ports = segment.merge_segment(0)
        # deleted handles and ports
        self.assertEqual(1, len(handles))
        self.assertEqual(2, len(ports))
        # handles and ports left after segment merging
        self.assertEqual(2, len(self.line.handles()))
        self.assertEqual(1, len(self.line.ports()))

        self.assertTrue(handles[0] not in self.line.handles())
        self.assertTrue(ports[0] not in self.line.ports())
        self.assertTrue(ports[1] not in self.line.ports())

        # old ports are completely removed as they are replaced by new one
        # port
        self.assertEqual(old_ports, ports)

        # finally, created port shall span between first and last handle
        port = self.line.ports()[0]
        self.assertEqual((0, 0), port.start.pos)
        self.assertEqual((20, 0), port.end.pos)

    def test_constraints_after_merge(self):
        """Test if constraints are recreated after line merge
        """

        # connect line2 to self.line
        line2 = Line()
        self.canvas.add(line2)
        head = line2.handles()[0]

        # conn = Connector(line2, head)
        # sink = conn.glue((25, 25))
        # assert sink is not None

        # conn.connect(sink)

        self.tool.connect(line2, head, (25, 25))
        cinfo = self.canvas.get_connection(head)
        self.assertEqual(self.line, cinfo.connected)

        segment = Segment(self.line, self.view)
        segment.split_segment(0)
        assert len(self.line.handles()) == 3
        c1 = cinfo.constraint

        segment.merge_segment(0)
        assert len(self.line.handles()) == 2

        h1, h2 = self.line.handles()
        # connection shall be reconstrained between 1st and 2nd handle
        cinfo = self.canvas.get_connection(head)
        self.assertEqual(cinfo.constraint._line[0]._point, h1.pos)
        self.assertEqual(cinfo.constraint._line[1]._point, h2.pos)
        self.assertFalse(c1 == cinfo.constraint)

    def test_merge_multiple(self):
        """Test multiple line merge
        """
        self.line.handles()[1].pos = (20, 16)
        segment = Segment(self.line, self.view)
        segment.split_segment(0, count=3)

        # start with 4 handles and 3 ports, merge 3 segments
        assert len(self.line.handles()) == 4
        assert len(self.line.ports()) == 3

        handles, ports = segment.merge_segment(0, count=3)
        self.assertEqual(2, len(handles))
        self.assertEqual(3, len(ports))
        self.assertEqual(2, len(self.line.handles()))
        self.assertEqual(1, len(self.line.ports()))

        self.assertTrue(not set(handles).intersection(set(self.line.handles())))
        self.assertTrue(not set(ports).intersection(set(self.line.ports())))

        # finally, created port shall span between first and last handle
        port = self.line.ports()[0]
        self.assertEqual((0, 0), port.start.pos)
        self.assertEqual((20, 16), port.end.pos)

    def test_merge_undo(self):
        """Test line merging undo
        """
        self.line.handles()[1].pos = (20, 0)

        segment = Segment(self.line, self.view)

        # split for merging
        segment.split_segment(0)
        assert len(self.line.handles()) == 3
        assert len(self.line.ports()) == 2

        # clear undo stack before merging
        del undo_list[:]

        # merge with empty undo stack
        segment.merge_segment(0)
        assert len(self.line.handles()) == 2
        assert len(self.line.ports()) == 1

        # after merge undo, 3 handles and 2 ports are expected again
        undo()
        self.assertEqual(3, len(self.line.handles()))
        self.assertEqual(2, len(self.line.ports()))

    def test_orthogonal_line_merge(self):
        """Test orthogonal line merging
        """
        self.assertEqual(4, len(self.canvas.solver._constraints))

        self.line.handles()[-1].pos = 100, 100

        segment = Segment(self.line, self.view)
        # prepare the self.line for merging
        segment.split_segment(0)
        segment.split_segment(0)
        self.line.orthogonal = True

        self.assertEqual(4 + 3, len(self.canvas.solver._constraints))
        self.assertEqual(4, len(self.line.handles()))
        self.assertEqual(3, len(self.line.ports()))

        # test the merging
        segment.merge_segment(0)

        self.assertEqual(4 + 2, len(self.canvas.solver._constraints))
        self.assertEqual(3, len(self.line.handles()))
        self.assertEqual(2, len(self.line.ports()))

    def test_params_errors(self):
        """Test parameter error exceptions
        """
        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        segment.split_segment(0)
        # no segment -1
        self.assertRaises(ValueError, segment.merge_segment, -1)

        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        segment.split_segment(0)
        # no segment no 2
        self.assertRaises(ValueError, segment.merge_segment, 2)

        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        segment.split_segment(0)
        # can't merge one or less segments :)
        self.assertRaises(ValueError, segment.merge_segment, 0, 1)

        line = Line()
        self.canvas.add(line)
        self.assertEqual(2, len(line.handles()))
        segment = Segment(line, self.view)
        # can't merge line with one segment
        self.assertRaises(ValueError, segment.merge_segment, 0)

        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        segment.split_segment(0)
        # 2 segments: no 0 and 1. cannot merge as there are no segments
        # after segment no 1
        self.assertRaises(ValueError, segment.merge_segment, 1)

        line = Line()
        self.canvas.add(line)
        segment = Segment(line, self.view)
        segment.split_segment(0)
        # 2 segments: no 0 and 1. cannot merge 3 segments as there are no 3
        # segments
        self.assertRaises(ValueError, segment.merge_segment, 0, 3)


class SegmentHandlesTest(unittest.TestCase):
    def setUp(self):
        self.canvas = Canvas()
        self.line = Line()
        self.canvas.add(self.line)
        self.view = View(self.canvas)

    def testHandleFinder(self):
        finder = HandleFinder(self.line, self.view)
        assert type(finder) is SegmentHandleFinder, type(finder)


# vim:sw=4:et:ai
