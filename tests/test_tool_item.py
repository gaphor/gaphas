import math

from gi.repository import Gtk

from gaphas.item import Element as Box
from gaphas.tool.itemtool import (
    DragState,
    handle_at_point,
    item_at_point,
    item_tool,
    on_drag_begin,
)


class MockEvent:
    def __init__(self, modifiers=0):
        self._modifiers = modifiers

    def get_state(self):
        return True, self._modifiers


class MockGesture:
    def __init__(self, view, event=MockEvent()):
        self._view = view
        self._event = event

    def get_widget(self):
        return self._view

    def get_last_event(self, _sequence):
        return self._event

    def get_current_event_state(self):
        return self._event.get_state()[1]

    def set_state(self, _state):
        pass


def test_should_create_a_gesture(view):
    tool = item_tool(view)

    assert isinstance(tool, Gtk.Gesture)


def test_select_item_on_click(view, box, window):
    tool = MockGesture(view)
    drag_state = DragState()
    selection = view.selection

    on_drag_begin(tool, 0, 0, drag_state)

    assert box is selection.focused_item
    assert box in selection.selected_items


def test_start_move_handle_on_click(view, box, window):
    tool = MockGesture(view)
    drag_state = DragState()

    on_drag_begin(tool, 0, 0, drag_state)

    assert drag_state.moving
    assert next(iter(drag_state.moving)).item is box
    assert next(iter(drag_state.moving)).handle is box.handles()[0]


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
    assert item_at_point(view, (10, 10), exclude=(box,)) is None


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
