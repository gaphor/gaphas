import pytest
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.guide import Guide, GuidedItemInMotion
from gaphas.item import Element, Line
from gaphas.view import GtkView


class Window(object):
    def __init__(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.window = Gtk.Window()
        self.window.add(self.view)
        self.window.show_all()
        self.line = Line()
        self.canvas.add(self.line)
        self.e1 = Element()
        self.e2 = Element()
        self.e3 = Element()


@pytest.fixture()
def win():
    test_window = Window()
    yield test_window
    test_window.window.destroy()


def test_find_closest(win):
    """Test find closest method.

    """
    set1 = [0, 10, 20]
    set2 = [2, 15, 30]

    guider = GuidedItemInMotion(Element(), win.view)
    d, closest = guider.find_closest(set1, set2)
    assert 2.0 == d
    assert [2.0] == closest


def test_element_guide():
    e1 = Element()
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


def test_line_guide(win):
    win.line.handles().append(win.line._create_handle((20, 20)))
    win.line.handles().append(win.line._create_handle((30, 30)))
    win.line.handles().append(win.line._create_handle((40, 40)))
    win.line.orthogonal = True
    win.canvas.update_now()

    guides = list(Guide(win.line).horizontal())
    assert 2 == len(guides)
    assert 10.0 == guides[0]
    assert 40.0 == guides[1]

    guides = list(Guide(win.line).vertical())
    assert 2 == len(guides)
    assert 00.0 == guides[0]
    assert 20.0 == guides[1]


def test_line_guide_horizontal(win):
    win.line.handles().append(win.line._create_handle((20, 20)))
    win.line.handles().append(win.line._create_handle((30, 30)))
    win.line.handles().append(win.line._create_handle((40, 40)))
    win.line.horizontal = True
    win.line.orthogonal = True
    win.canvas.update_now()

    guides = list(Guide(win.line).horizontal())
    assert 2 == len(guides)
    assert 0.0 == guides[0]
    assert 20.0 == guides[1]

    guides = list(Guide(win.line).horizontal())
    assert 2 == len(guides)
    assert 0.0 == guides[0]
    assert 20.0 == guides[1]


def test_guide_item_in_motion(win):
    win.canvas.add(win.e1)
    win.canvas.add(win.e2)
    win.canvas.add(win.e3)

    assert 0 == win.e1.matrix[4]
    assert 0 == win.e1.matrix[5]

    win.e2.matrix.translate(40, 40)
    win.e2.request_update()
    assert 40 == win.e2.matrix[4]
    assert 40 == win.e2.matrix[5]

    guider = GuidedItemInMotion(win.e3, win.view)

    guider.start_move((0, 0))
    assert 0 == win.e3.matrix[4]
    assert 0 == win.e3.matrix[5]

    # Moved back to guided lines:
    for d in range(0, 3):
        guider.move((d, d))
        assert 0 == win.e3.matrix[4]
        assert 0 == win.e3.matrix[5]

    for d in range(3, 5):
        guider.move((d, d))
        assert 5 == win.e3.matrix[4]
        assert 5 == win.e3.matrix[5]

    guider.move((20, 20))
    assert 20 == win.e3.matrix[4]
    assert 20 == win.e3.matrix[5]


def test_guide_item_in_motion_2(win):
    win.canvas.add(win.e1)
    win.canvas.add(win.e2)
    win.canvas.add(win.e3)

    assert 0 == win.e1.matrix[4]
    assert 0 == win.e1.matrix[5]

    win.e2.matrix.translate(40, 40)
    win.e2.request_update()
    assert 40 == win.e2.matrix[4]
    assert 40 == win.e2.matrix[5]

    guider = GuidedItemInMotion(win.e3, win.view)

    guider.start_move((3, 3))
    assert 0 == win.e3.matrix[4]
    assert 0 == win.e3.matrix[5]

    # Moved back to guided lines:
    for y in range(4, 6):
        guider.move((3, y))
        assert 0 == win.e3.matrix[4]
        assert 0 == win.e3.matrix[5]

    for y in range(6, 9):
        guider.move((3, y))
        assert 0 == win.e3.matrix[4]
        assert 5 == win.e3.matrix[5]

    # Take into account initial cursor offset of (3, 3)
    guider.move((20, 23))
    assert 17 == win.e3.matrix[4]
    assert 20 == win.e3.matrix[5]
