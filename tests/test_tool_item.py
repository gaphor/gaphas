from gi.repository import Gtk

from gaphas.tool.itemtool import DragState, item_tool, on_drag_begin


class MockEvent:
    def __init__(self, modifiers=0):
        self._modifiers = modifiers

    def get_state(self):
        return True, self._modifiers


class MockGesture:
    def __init__(self, event=MockEvent()):
        self._event = event

    def get_last_event(self, _sequence):
        return self._event


def test_should_create_a_gesture(view):
    tool = item_tool(view)

    assert isinstance(tool, Gtk.Gesture)


def test_select__hovered_item_on_click(view, box):
    gesture = MockGesture()
    drag_state = DragState()
    selection = view.selection

    on_drag_begin(gesture, 0, 0, view, drag_state)

    assert box is selection.focused_item
    assert box in selection.selected_items
