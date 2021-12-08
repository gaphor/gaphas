import pytest

from gaphas.connector import ConnectionSink
from gaphas.item import Element


@pytest.fixture
def element(connections):
    """Element at (0, 0), size 100x100."""
    return Element(connections, 100, 100)


@pytest.mark.parametrize(
    "pos,expected_glue_pos",
    [
        [(0, 0), (0, 0)],
        [(50, 0), (50, 0)],
        [(0, 50), (0, 50)],
        [(50, 100), (50, 100)],
        [(100, 50), (100, 50)],
        [(-50, 0), None],
        [(50, 50), None],
    ],
)
def test_element_glue_on_border(element, pos, expected_glue_pos):
    sink = ConnectionSink(element)
    glue_pos = sink.glue(pos)

    assert glue_pos == expected_glue_pos


@pytest.mark.parametrize(
    "secondary_pos,expected_glue_pos",
    [
        [(-50, 0), (0.5, 25.5)],
        [(0, -50), (25.5, 0.5)],
        [(50, 150), (50.5, 100.5)],
        [(150, 50), (100.5, 50.5)],
    ],
)
def test_element_glue_on_border_with_secondary_position(
    element, secondary_pos, expected_glue_pos
):
    pos = (50, 50)
    sink = ConnectionSink(element)
    glue_pos = sink.glue(pos, secondary_pos=secondary_pos)

    assert glue_pos == expected_glue_pos
