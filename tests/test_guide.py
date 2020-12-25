import pytest

from gaphas.connections import Connections
from gaphas.connector import Handle
from gaphas.guide import Guide, GuidedItemMove
from gaphas.item import Element, Line
from gaphas.solver import WEAK


@pytest.fixture
def line(canvas, connections):
    line = Line(connections)
    canvas.add(line)
    return line


def test_find_closest(view, connections):
    """Test find closest method."""
    set1 = [0, 10, 20]
    set2 = [2, 15, 30]

    guider = GuidedItemMove(Element(connections), view)
    d, closest = guider.find_closest(set1, set2)
    assert 2.0 == d
    assert [2.0] == closest


def test_element_guide():
    e1 = Element(Connections())
    assert 10 == e1.width
    assert 10 == e1.height
    guides = Guide(e1).horizontal()
    assert 0.0 == guides[0]
    assert 5.0 == guides[1]
    assert 10.0 == guides[2]
    guides = Guide(e1).vertical()
    assert 0.0 == guides[0]
    assert 5.0 == guides[1]
    assert 10.0 == guides[2]


def test_line_guide(line, canvas):
    line.handles().append(Handle((20, 20), strength=WEAK))
    line.handles().append(Handle((30, 30), strength=WEAK))
    line.handles().append(Handle((40, 40), strength=WEAK))
    line.orthogonal = True
    canvas.update_now((line,))

    guides = list(Guide(line).horizontal())
    assert 2 == len(guides)
    assert 10.0 == guides[0]
    assert 40.0 == guides[1]

    guides = list(Guide(line).vertical())
    assert 2 == len(guides)
    assert 10.0 == guides[0]
    assert 30.0 == guides[1]


def test_line_guide_horizontal(line, canvas):
    line.handles().append(Handle((20, 20)))
    line.handles().append(Handle((30, 30)))
    line.handles().append(Handle((40, 40)))
    line.horizontal = True
    line.orthogonal = True
    canvas.update_now((line,))

    guides = list(Guide(line).horizontal())
    assert 2 == len(guides)
    assert 10.0 == guides[0]
    assert 30.0 == guides[1]

    guides = list(Guide(line).horizontal())
    assert 2 == len(guides)
    assert 10.0 == guides[0]
    assert 30.0 == guides[1]


def test_guide_item_in_motion(connections, canvas, view, window):
    e1 = Element(connections)
    e2 = Element(connections)
    e3 = Element(connections)
    canvas.add(e1)
    canvas.add(e2)
    canvas.add(e3)

    assert 0 == e1.matrix()[4]
    assert 0 == e1.matrix()[5]

    e2.matrix().translate(40, 40)
    canvas.request_update(e2)
    assert 40 == e2.matrix()[4]
    assert 40 == e2.matrix()[5]

    guider = GuidedItemMove(e3, view)

    guider.start_move((0, 0))
    assert 0 == e3.matrix()[4]
    assert 0 == e3.matrix()[5]

    # Moved back to guided lines:
    for d in range(3):
        guider.move((d, d))
        assert 0 == e3.matrix()[4]
        assert 0 == e3.matrix()[5]

    guider.move((20, 20))
    assert 20 == e3.matrix()[4]
    assert 20 == e3.matrix()[5]


def test_guide_item_in_motion_2(connections, canvas, view):
    e1 = Element(connections)
    e2 = Element(connections)
    e3 = Element(connections)
    canvas.add(e1)
    canvas.add(e2)
    canvas.add(e3)

    assert 0 == e1.matrix()[4]
    assert 0 == e1.matrix()[5]

    e2.matrix().translate(40, 40)
    canvas.request_update(e2)
    assert 40 == e2.matrix()[4]
    assert 40 == e2.matrix()[5]

    guider = GuidedItemMove(e3, view)

    guider.start_move((3, 3))
    assert 0 == e3.matrix()[4]
    assert 0 == e3.matrix()[5]

    # Moved back to guided lines:
    for y in range(4, 6):
        guider.move((3, y))
        assert 0 == e3.matrix()[4]
        assert 0 == e3.matrix()[5]

    # Take into account initial cursor offset of (3, 3)
    guider.move((20, 23))
    assert 17 == e3.matrix()[4]
    assert 20 == e3.matrix()[5]
