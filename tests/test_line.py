"""Basic item tests for lines."""

from gaphas.canvas import Canvas
from gaphas.item import Line
from gaphas.segment import Segment


def test_initial_ports():
    """Test initial ports amount."""
    canvas = Canvas()
    line = Line(canvas.connections)
    assert 1 == len(line.ports())


def test_orthogonal_horizontal_undo(revert_undo, undo_fixture):
    """Test orthogonal line constraints bug (#107)."""
    canvas = Canvas()
    line = Line(canvas.connections)
    canvas.add(line)
    assert not line.horizontal
    assert len(canvas.solver._constraints) == 0

    segment = Segment(line, canvas)
    segment.split_segment(0)

    line.orthogonal = True

    assert 2 == len(canvas.solver._constraints)

    del undo_fixture[2][:]  # Clear undo_list
    line.horizontal = True

    assert 2 == len(canvas.solver._constraints)

    undo_fixture[0]()  # Call undo

    assert not line.horizontal
    assert 2 == len(canvas.solver._constraints)

    line.horizontal = True

    assert line.horizontal
    assert 2 == len(canvas.solver._constraints)


def test_orthogonal_line_undo(revert_undo, undo_fixture):
    """Test orthogonal line undo."""
    canvas = Canvas()
    line = Line(canvas.connections)
    canvas.add(line)

    segment = Segment(line, canvas)
    segment.split_segment(0)

    # Start with no orthogonal constraints
    assert len(canvas.solver._constraints) == 0

    line.orthogonal = True

    # Check orthogonal constraints
    assert 2 == len(canvas.solver._constraints)
    assert 3 == len(line.handles())

    undo_fixture[0]()  # Call undo

    assert not line.orthogonal
    assert 0 == len(canvas.solver._constraints)
    assert 2 == len(line.handles())
