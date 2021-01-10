"""Basic item tests for lines."""

from gaphas.canvas import Canvas
from gaphas.item import Line


def test_initial_ports():
    """Test initial ports amount."""
    canvas = Canvas()
    line = Line(canvas.connections)
    assert 1 == len(line.ports())
