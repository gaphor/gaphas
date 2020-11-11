import math

from gaphas.aspect.finder import handle_at_point, item_at_point
from gaphas.item import Element as Box


def test_get_item_at_point(view, box):
    """Hover tool only reacts on motion-notify events."""
    box.width = 50
    box.height = 50

    assert item_at_point(view, (10, 10)) is box
    assert item_at_point(view, (60, 10)) is None


def test_get_unselected_item_at_point(view, box):
    box.width = 50
    box.height = 50
    view.selection.select_items(box)

    assert item_at_point(view, (10, 10)) is box
    assert item_at_point(view, (10, 10), selected=False) is None


def test_get_handle_at_point(view, canvas, connections):
    box = Box(connections)
    box.min_width = 20
    box.min_height = 30
    box.matrix.translate(20, 20)
    box.matrix.rotate(math.pi / 1.5)
    canvas.add(box)

    i, h = handle_at_point(view, (20, 20))
    assert i is box
    assert h is box.handles()[0]


def test_get_handle_at_point_at_pi_div_2(view, canvas, connections):
    box = Box(connections)
    box.min_width = 20
    box.min_height = 30
    box.matrix.translate(20, 20)
    box.matrix.rotate(math.pi / 2)
    canvas.add(box)

    i, h = handle_at_point(view, (20, 20))
    assert i is box
    assert h is box.handles()[0]
