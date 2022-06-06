from gi.repository import Gtk

from gaphas.view import GtkView


class PanState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pos = None


def pan_tool(view: GtkView) -> Gtk.GestureDrag:
    gesture = (
        Gtk.GestureDrag.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.GestureDrag.new()
    )
    gesture.set_button(2)
    pan_state = PanState()
    gesture.connect("drag-begin", on_drag_begin, pan_state)
    gesture.connect("drag-update", on_drag_update, pan_state)
    return gesture


def on_drag_begin(gesture, _start_x, _start_y, pan_state):
    view = gesture.get_widget()
    m = view.matrix
    pan_state.pos = (m[4], m[5])
    gesture.set_state(Gtk.EventSequenceState.CLAIMED)


def on_drag_update(gesture, offset_x, offset_y, pan_state):
    view = gesture.get_widget()
    m = view.matrix
    x0, y0 = pan_state.pos
    m.translate(x0 + offset_x - m[4], y0 + offset_y - m[5])
