import pytest

from gaphas.item import NE, NW, SE, SW


def test_creation_with_size(canvas, box):
    """Test if initial size holds when added to a canvas."""
    box.width = 150
    box.height = 153

    assert box.width == 150, box.width
    assert box.height == 153, box.height
    assert box.handles()[SE].pos.x == 150, box.handles()[SE].pos.x
    assert box.handles()[SE].pos.y == 153, box.handles()[SE].pos.y


def test_box_handle_order(box):
    h_nw, h_ne, h_se, h_sw = box.handles()
    assert h_nw is box.handles()[NW]
    assert h_ne is box.handles()[NE]
    assert h_sw is box.handles()[SW]
    assert h_se is box.handles()[SE]


@pytest.mark.parametrize("count", [1, 2, 10, 99])
def test_resize_by_dragging_se_handle(canvas, box, count):
    h_nw, h_ne, h_se, h_sw = box.handles()

    for _ in range(count):
        h_se.pos.x += 100  # h.se.{x,y} = 10, now
        h_se.pos.y += 100
        canvas.update_now((box,))

    assert 100 * count + 10 == h_se.pos.x
    assert 100 * count + 10 == float(h_se.pos.y)

    assert 100 * count + 10 == float(h_ne.pos.x)
    assert 100 * count + 10 == float(h_sw.pos.y)
