"""Test segment aspects for items.

"""
import pytest

from gaphas.canvas import Canvas
from gaphas.item import Item
from gaphas.segment import *
from gaphas.view import View


class SegmentFixture:
    def __init__(self):
        self.canvas = Canvas()
        self.line = Line()
        self.canvas.add(self.line)
        self.view = View(self.canvas)
        self.item = Item()


@pytest.fixture(name="seg")
def segment_fixture():
    return SegmentFixture()


def test_segment_fails_for_item(seg):
    """Test if Segment aspect can be applied to Item.

    """
    try:
        Segment(seg.item, seg.view)
    except TypeError:
        pass
    else:
        assert False, "Should not be reached"


def test_segment(seg):
    """Test add a new segment to a line.

    """
    line = Line()
    seg.canvas.add(line)
    segment = Segment(line, seg.view)
    assert 2 == len(line.handles())
    segment.split((5, 5))
    assert 3 == len(line.handles())


# Test Line Splitting


def test_split_single(simple_canvas):
    """Test single line splitting
    """
    # Start with 2 handles & 1 port, after split: expect 3 handles & 2 ports
    assert len(simple_canvas.line.handles()) == 2
    assert len(simple_canvas.line.ports()) == 1

    old_port = simple_canvas.line.ports()[0]
    h1, h2 = simple_canvas.line.handles()
    assert h1.pos == old_port.start
    assert h2.pos == old_port.end

    segment = Segment(simple_canvas.line, simple_canvas.view)

    handles, ports = segment.split_segment(0)
    handle = handles[0]
    assert 1 == len(handles)
    assert (50, 50) == handle.pos.pos
    assert 3 == len(simple_canvas.line.handles())
    assert 2 == len(simple_canvas.line.ports())

    # New handle is between old handles
    assert handle == simple_canvas.line.handles()[1]
    # The old port is deleted
    assert old_port not in simple_canvas.line.ports()

    # check ports order
    p1, p2 = simple_canvas.line.ports()
    h1, h2, h3 = simple_canvas.line.handles()
    assert h1.pos == p1.start
    assert h2.pos == p1.end
    assert h2.pos == p2.start
    assert h3.pos == p2.end


def test_split_multiple(simple_canvas):
    """Test multiple line splitting.

    """
    simple_canvas.line.handles()[1].pos = (20, 16)
    handles = simple_canvas.line.handles()
    old_ports = simple_canvas.line.ports()[:]

    # Start with two handles, split into 4 segments: expect 3 new handles
    assert len(handles) == 2
    assert len(old_ports) == 1

    segment = Segment(simple_canvas.line, simple_canvas.view)

    handles, ports = segment.split_segment(0, count=4)
    assert 3 == len(handles)
    h1, h2, h3 = handles
    assert (5, 4) == h1.pos.pos
    assert (10, 8) == h2.pos.pos
    assert (15, 12) == h3.pos.pos

    # New handles between old handles
    assert 5 == len(simple_canvas.line.handles())
    assert h1 == simple_canvas.line.handles()[1]
    assert h2 == simple_canvas.line.handles()[2]
    assert h3 == simple_canvas.line.handles()[3]

    assert 4 == len(simple_canvas.line.ports())

    # The old port is deleted
    assert old_ports[0] not in simple_canvas.line.ports()

    # Check ports order
    p1, p2, p3, p4 = simple_canvas.line.ports()
    h1, h2, h3, h4, h5 = simple_canvas.line.handles()
    assert h1.pos == p1.start
    assert h2.pos == p1.end
    assert h2.pos == p2.start
    assert h3.pos == p2.end
    assert h3.pos == p3.start
    assert h4.pos == p3.end
    assert h4.pos == p4.start
    assert h5.pos == p4.end


def test_ports_after_split(simple_canvas):
    """Test ports removal after split
    """
    simple_canvas.line.handles()[1].pos = (20, 16)

    segment = Segment(simple_canvas.line, simple_canvas.view)

    segment.split_segment(0)
    handles = simple_canvas.line.handles()
    old_ports = simple_canvas.line.ports()[:]

    # Start with 3 handles and 2 ports
    assert len(handles) == 3
    assert len(old_ports) == 2

    # Split 1st segment again: 1st port should be deleted, but 2nd one should
    # remain untouched
    segment.split_segment(0)
    assert old_ports[0] not in simple_canvas.line.ports()
    assert old_ports[1] == simple_canvas.line.ports()[2]


def test_constraints_after_split(simple_canvas):
    """Test if constraints are recreated after line split.

    """
    # Connect line2 to self.line
    line2 = Line()
    simple_canvas.canvas.add(line2)
    head = line2.handles()[0]
    simple_canvas.tool.connect(line2, head, (25, 25))
    cinfo = simple_canvas.canvas.get_connection(head)
    assert simple_canvas.line == cinfo.connected

    Segment(simple_canvas.line, simple_canvas.view).split_segment(0)
    assert len(simple_canvas.line.handles()) == 3
    h1, h2, h3 = simple_canvas.line.handles()

    cinfo = simple_canvas.canvas.get_connection(head)
    # Connection shall be reconstrained between 1st and 2nd handle
    assert h1.pos == cinfo.constraint._line[0]._point
    assert h2.pos == cinfo.constraint._line[1]._point


def test_split_undo(simple_canvas, revert_undo, undo_fixture):
    """Test line splitting undo.

    """
    simple_canvas.line.handles()[1].pos = (20, 0)

    # We start with two handles and one port, after split 3 handles and
    # 2 ports are expected
    assert len(simple_canvas.line.handles()) == 2
    assert len(simple_canvas.line.ports()) == 1

    segment = Segment(simple_canvas.line, simple_canvas.view)
    segment.split_segment(0)
    assert len(simple_canvas.line.handles()) == 3
    assert len(simple_canvas.line.ports()) == 2

    # After undo, 2 handles and 1 port are expected again
    undo_fixture[0]()  # Call Undo
    assert 2 == len(simple_canvas.line.handles())
    assert 1 == len(simple_canvas.line.ports())


def test_orthogonal_line_split(simple_canvas):
    """Test orthogonal line splitting.

    """
    # Start with no orthogonal constraints
    assert len(simple_canvas.line._orthogonal_constraints) == 0

    segment = Segment(simple_canvas.line, None)
    segment.split_segment(0)

    simple_canvas.line.orthogonal = True

    # Check orthogonal constraints
    assert 2 == len(simple_canvas.line._orthogonal_constraints)
    assert 3 == len(simple_canvas.line.handles())

    Segment(simple_canvas.line, simple_canvas.view).split_segment(0)

    # 3 handles and 2 ports are expected
    # 2 constraints keep the self.line orthogonal
    assert 3 == len(simple_canvas.line._orthogonal_constraints)
    assert 4 == len(simple_canvas.line.handles())
    assert 3 == len(simple_canvas.line.ports())


def test_params_error_exc(simple_canvas):
    """Test parameter error exceptions.

    """
    line = Line()
    segment = Segment(line, simple_canvas.view)

    # There is only 1 segment
    with pytest.raises(ValueError):
        segment.split_segment(-1)

    line = Line()
    segment = Segment(line, simple_canvas.view)
    with pytest.raises(ValueError):
        segment.split_segment(1)

    line = Line()
    # Can't split into one or less segment :)
    segment = Segment(line, simple_canvas.view)
    with pytest.raises(ValueError):
        segment.split_segment(0, 1)


# Test Line Merging


def test_merge_first_single(simple_canvas):
    """Test single line merging starting from 1st segment.

    """
    simple_canvas.line.handles()[1].pos = (20, 0)
    segment = Segment(simple_canvas.line, simple_canvas.view)
    segment.split_segment(0)

    # We start with 3 handles and 2 ports, after merging 2 handles and 1 port
    # are expected
    assert len(simple_canvas.line.handles()) == 3
    assert len(simple_canvas.line.ports()) == 2
    old_ports = simple_canvas.line.ports()[:]

    segment = Segment(simple_canvas.line, simple_canvas.view)
    handles, ports = segment.merge_segment(0)
    # Deleted handles and ports
    assert 1 == len(handles)
    assert 2 == len(ports)
    # Handles and ports left after segment merging
    assert 2 == len(simple_canvas.line.handles())
    assert 1 == len(simple_canvas.line.ports())

    assert handles[0] not in simple_canvas.line.handles()
    assert ports[0] not in simple_canvas.line.ports()
    assert ports[1] not in simple_canvas.line.ports()

    # Old ports are completely removed as they are replaced by new one port
    assert old_ports == ports

    # Finally, created port shall span between first and last handle
    port = simple_canvas.line.ports()[0]
    assert (0, 0) == port.start.pos
    assert (20, 0) == port.end.pos


def test_constraints_after_merge(simple_canvas):
    """Test if constraints are recreated after line merge.

    """
    line2 = Line()
    simple_canvas.canvas.add(line2)
    head = line2.handles()[0]

    simple_canvas.tool.connect(line2, head, (25, 25))
    cinfo = simple_canvas.canvas.get_connection(head)
    assert simple_canvas.line == cinfo.connected

    segment = Segment(simple_canvas.line, simple_canvas.view)
    segment.split_segment(0)
    assert len(simple_canvas.line.handles()) == 3
    c1 = cinfo.constraint

    segment.merge_segment(0)
    assert len(simple_canvas.line.handles()) == 2

    h1, h2 = simple_canvas.line.handles()
    # Connection shall be reconstrained between 1st and 2nd handle
    cinfo = simple_canvas.canvas.get_connection(head)
    assert cinfo.constraint._line[0]._point == h1.pos
    assert cinfo.constraint._line[1]._point == h2.pos
    assert c1 != cinfo.constraint


def test_merge_multiple(simple_canvas):
    """Test multiple line merge.

    """
    simple_canvas.line.handles()[1].pos = (20, 16)
    segment = Segment(simple_canvas.line, simple_canvas.view)
    segment.split_segment(0, count=3)

    # Start with 4 handles and 3 ports, merge 3 segments
    assert len(simple_canvas.line.handles()) == 4
    assert len(simple_canvas.line.ports()) == 3

    handles, ports = segment.merge_segment(0, count=3)
    assert 2 == len(handles)
    assert 3 == len(ports)
    assert 2 == len(simple_canvas.line.handles())
    assert 1 == len(simple_canvas.line.ports())

    assert not set(handles).intersection(set(simple_canvas.line.handles()))
    assert not set(ports).intersection(set(simple_canvas.line.ports()))

    # Finally, the created port shall span between first and last handle
    port = simple_canvas.line.ports()[0]
    assert (0, 0) == port.start.pos
    assert (20, 16) == port.end.pos


def test_merge_undo(simple_canvas, revert_undo, undo_fixture):
    """Test line merging undo.

    """
    simple_canvas.line.handles()[1].pos = (20, 0)

    segment = Segment(simple_canvas.line, simple_canvas.view)

    # Split for merging
    segment.split_segment(0)
    assert len(simple_canvas.line.handles()) == 3
    assert len(simple_canvas.line.ports()) == 2

    # Clear undo stack before merging
    del undo_fixture[2][:]

    # Merge with empty undo stack
    segment.merge_segment(0)
    assert len(simple_canvas.line.handles()) == 2
    assert len(simple_canvas.line.ports()) == 1

    # After merge undo, 3 handles and 2 ports are expected again
    undo_fixture[0]()  # Undo
    assert 3 == len(simple_canvas.line.handles())
    assert 2 == len(simple_canvas.line.ports())


def test_orthogonal_line_merge(simple_canvas):
    """Test orthogonal line merging.

    """
    assert 12 == len(simple_canvas.canvas.solver._constraints)

    simple_canvas.line.handles()[-1].pos = 100, 100

    segment = Segment(simple_canvas.line, simple_canvas.view)
    # Prepare the self.line for merging
    segment.split_segment(0)
    segment.split_segment(0)
    simple_canvas.line.orthogonal = True

    assert 6 + 6 + 3 == len(simple_canvas.canvas.solver._constraints)
    assert 4 == len(simple_canvas.line.handles())
    assert 3 == len(simple_canvas.line.ports())

    # Test the merging
    segment.merge_segment(0)

    assert 6 + 6 + 2 == len(simple_canvas.canvas.solver._constraints)
    assert 3 == len(simple_canvas.line.handles())
    assert 2 == len(simple_canvas.line.ports())


@pytest.mark.parametrize("num_segments", [-1, 2, (0, 1), 0, 1, (0, 3)])
def test_params_errors(simple_canvas, num_segments):
    """Test parameter error exceptions.

    """
    line = Line()
    simple_canvas.canvas.add(line)
    segment = Segment(line, simple_canvas.view)
    with pytest.raises(ValueError):
        if isinstance(num_segments, tuple):
            segment.split_segment(0)
            segment.merge_segment(num_segments[0], num_segments[1])
        elif num_segments == 0:
            assert 2 == len(line.handles())
            segment.merge_segment(0)
        else:
            segment.split_segment(0)
            segment.merge_segment(num_segments)


def test_handle_finder(seg):
    finder = HandleFinder(seg.line, seg.view)
    assert type(finder) is SegmentHandleFinder, type(finder)
