"""Test segment aspects for items."""
import pytest

from gaphas.aspect import HandleMove
from gaphas.item import Element
from gaphas.segment import Line, Segment


def test_segment_fails_for_element(canvas, connections):
    item = Element(connections)
    with pytest.raises(TypeError):
        Segment(canvas, item)


def test_add_segment_to_line(canvas, connections):
    line = Line(connections)
    canvas.add(line)
    segment = Segment(line, canvas)
    assert 2 == len(line.handles())
    segment.split((5, 5))
    assert 3 == len(line.handles())


# Test Line Splitting


def test_split_single(canvas, line):
    # Start with 2 handles & 1 port, after split: expect 3 handles & 2 ports
    assert len(line.handles()) == 2
    assert len(line.ports()) == 1

    old_port = line.ports()[0]
    h1, h2 = line.handles()
    assert h1.pos == old_port.start
    assert h2.pos == old_port.end

    segment = Segment(line, canvas)

    handles, ports = segment.split_segment(0)
    handle = handles[0]
    assert 1 == len(handles)
    assert (50, 50) == handle.pos.pos
    assert 3 == len(line.handles())
    assert 2 == len(line.ports())

    # New handle is between old handles
    assert handle == line.handles()[1]
    # The old port is deleted
    assert old_port not in line.ports()

    # check ports order
    p1, p2 = line.ports()
    h1, h2, h3 = line.handles()
    assert h1.pos == p1.start
    assert h2.pos == p1.end
    assert h2.pos == p2.start
    assert h3.pos == p2.end


def test_split_multiple(canvas, line):
    """Test multiple line splitting."""
    line.handles()[1].pos = (20, 16)
    handles = line.handles()
    old_ports = line.ports()[:]

    # Start with two handles, split into 4 segments: expect 3 new handles
    assert len(handles) == 2
    assert len(old_ports) == 1

    segment = Segment(line, canvas)

    handles, ports = segment.split_segment(0, count=4)
    assert 3 == len(handles)
    h1, h2, h3 = handles
    assert (5, 4) == h1.pos.pos
    assert (10, 8) == h2.pos.pos
    assert (15, 12) == h3.pos.pos

    # New handles between old handles
    assert 5 == len(line.handles())
    assert h1 == line.handles()[1]
    assert h2 == line.handles()[2]
    assert h3 == line.handles()[3]

    assert 4 == len(line.ports())

    # The old port is deleted
    assert old_ports[0] not in line.ports()

    # Check ports order
    p1, p2, p3, p4 = line.ports()
    h1, h2, h3, h4, h5 = line.handles()
    assert h1.pos == p1.start
    assert h2.pos == p1.end
    assert h2.pos == p2.start
    assert h3.pos == p2.end
    assert h3.pos == p3.start
    assert h4.pos == p3.end
    assert h4.pos == p4.start
    assert h5.pos == p4.end


def test_ports_after_split(canvas, line):
    """Test ports removal after split."""
    line.handles()[1].pos = (20, 16)

    segment = Segment(line, canvas)

    segment.split_segment(0)
    handles = line.handles()
    old_ports = line.ports()[:]

    # Start with 3 handles and 2 ports
    assert len(handles) == 3
    assert len(old_ports) == 2

    # Split 1st segment again: 1st port should be deleted, but 2nd one should
    # remain untouched
    segment.split_segment(0)
    assert old_ports[0] not in line.ports()
    assert old_ports[1] == line.ports()[2]


def test_constraints_after_split(canvas, connections, line, view):
    """Test if constraints are recreated after line split."""
    # Connect line2 to self.line
    line2 = Line(connections)
    canvas.add(line2)
    head = line2.handles()[0]
    HandleMove(line2, head, view).connect((25, 25))
    cinfo = canvas.connections.get_connection(head)
    assert line == cinfo.connected
    orig_constraint = cinfo.constraint

    Segment(line, canvas).split_segment(0)
    assert len(line.handles()) == 3
    h1, h2, h3 = line.handles()

    cinfo = canvas.connections.get_connection(head)
    assert cinfo.constraint != orig_constraint


def test_split_undo(canvas, line, revert_undo, undo_fixture):
    """Test line splitting undo."""
    line.handles()[1].pos = (20, 0)

    # We start with two handles and one port, after split 3 handles and
    # 2 ports are expected
    assert len(line.handles()) == 2
    assert len(line.ports()) == 1

    segment = Segment(line, canvas)
    segment.split_segment(0)
    assert len(line.handles()) == 3
    assert len(line.ports()) == 2

    # After undo, 2 handles and 1 port are expected again
    undo_fixture[0]()  # Call Undo
    assert 2 == len(line.handles())
    assert 1 == len(line.ports())


def test_orthogonal_line_split(canvas, line):
    """Test orthogonal line splitting."""
    # Start with no orthogonal constraints
    assert len(line._orthogonal_constraints) == 0

    segment = Segment(line, canvas)
    segment.split_segment(0)

    line.orthogonal = True

    # Check orthogonal constraints
    assert 2 == len(line._orthogonal_constraints)
    assert 3 == len(line.handles())

    Segment(line, canvas).split_segment(0)

    # 3 handles and 2 ports are expected
    # 2 constraints keep the self.line orthogonal
    assert 3 == len(line._orthogonal_constraints)
    assert 4 == len(line.handles())
    assert 3 == len(line.ports())


def test_params_error_exc(canvas, connections):
    """Test parameter error exceptions."""
    line = Line(connections)
    segment = Segment(line, canvas)

    # There is only 1 segment
    with pytest.raises(ValueError):
        segment.split_segment(-1)

    line = Line(connections)
    segment = Segment(line, canvas)
    with pytest.raises(ValueError):
        segment.split_segment(1)

    line = Line(connections)
    # Can't split into one or less segment :)
    segment = Segment(line, canvas)
    with pytest.raises(ValueError):
        segment.split_segment(0, 1)


# Test Line Merging


def test_merge_first_single(line, canvas, view):
    """Test single line merging starting from 1st segment."""
    line.handles()[1].pos = (20, 0)
    segment = Segment(line, canvas)
    segment.split_segment(0)

    # We start with 3 handles and 2 ports, after merging 2 handles and 1 port
    # are expected
    assert len(line.handles()) == 3
    assert len(line.ports()) == 2
    old_ports = line.ports()[:]

    segment = Segment(line, canvas)
    handles, ports = segment.merge_segment(0)
    # Deleted handles and ports
    assert 1 == len(handles)
    assert 2 == len(ports)
    # Handles and ports left after segment merging
    assert 2 == len(line.handles())
    assert 1 == len(line.ports())

    assert handles[0] not in line.handles()
    assert ports[0] not in line.ports()
    assert ports[1] not in line.ports()

    # Old ports are completely removed as they are replaced by new one port
    assert old_ports == ports

    # Finally, created port shall span between first and last handle
    port = line.ports()[0]
    assert (0, 0) == port.start.pos
    assert (20, 0) == port.end.pos


def test_constraints_after_merge(canvas, connections, line, view):
    """Test if constraints are recreated after line merge."""
    line2 = Line(connections)
    canvas.add(line2)
    head = line2.handles()[0]

    canvas.request_update(line)
    canvas.request_update(line2)
    view.update()

    HandleMove(line2, head, view).connect((25, 25))
    cinfo = connections.get_connection(head)
    assert line == cinfo.connected

    segment = Segment(line, canvas)
    segment.split_segment(0)
    assert len(line.handles()) == 3
    orig_constraint = cinfo.constraint

    segment.merge_segment(0)
    assert len(line.handles()) == 2

    h1, h2 = line.handles()
    # Connection shall be reconstrained between 1st and 2nd handle
    cinfo = canvas.connections.get_connection(head)
    assert orig_constraint != cinfo.constraint


def test_merge_multiple(canvas, line):
    """Test multiple line merge."""
    line.handles()[1].pos = (20, 16)
    segment = Segment(line, canvas)
    segment.split_segment(0, count=3)

    # Start with 4 handles and 3 ports, merge 3 segments
    assert len(line.handles()) == 4
    assert len(line.ports()) == 3

    handles, ports = segment.merge_segment(0, count=3)
    assert 2 == len(handles)
    assert 3 == len(ports)
    assert 2 == len(line.handles())
    assert 1 == len(line.ports())

    assert not set(handles).intersection(set(line.handles()))
    assert not set(ports).intersection(set(line.ports()))

    # Finally, the created port shall span between first and last handle
    port = line.ports()[0]
    assert (0, 0) == port.start.pos
    assert (20, 16) == port.end.pos


def test_merge_undo(canvas, line, revert_undo, undo_fixture):
    """Test line merging undo."""
    line.handles()[1].pos = (20, 0)

    segment = Segment(line, canvas)

    # Split for merging
    segment.split_segment(0)
    assert len(line.handles()) == 3
    assert len(line.ports()) == 2

    # Clear undo stack before merging
    del undo_fixture[2][:]

    # Merge with empty undo stack
    segment.merge_segment(0)
    assert len(line.handles()) == 2
    assert len(line.ports()) == 1

    # After merge undo, 3 handles and 2 ports are expected again
    undo_fixture[0]()  # Undo
    assert 3 == len(line.handles())
    assert 2 == len(line.ports())


def test_orthogonal_line_merge(canvas, connections, line):
    """Test orthogonal line merging."""
    assert 0 == len(connections.solver._constraints)

    line.handles()[-1].pos = 100, 100

    segment = Segment(line, canvas)
    # Prepare the self.line for merging
    segment.split_segment(0)
    segment.split_segment(0)
    line.orthogonal = True

    assert 3 == len(connections.solver._constraints)
    assert 4 == len(line.handles())
    assert 3 == len(line.ports())

    # Test the merging
    segment.merge_segment(0)

    assert 2 == len(connections.solver._constraints)
    assert 3 == len(line.handles())
    assert 2 == len(line.ports())


@pytest.mark.parametrize("num_segments", [-1, 2, (0, 1), 0, 1, (0, 3)])
def test_params_errors(canvas, connections, num_segments):
    """Test parameter error exceptions."""
    line = Line(connections)
    canvas.add(line)
    segment = Segment(line, canvas)
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
