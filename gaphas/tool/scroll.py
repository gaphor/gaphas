from gi.repository import Gdk, Gtk

from gaphas.tool.zoom import Zoom
from gaphas.tool.hover import set_cursor


def scroll_tools(speed: int = 10) -> Gtk.EventControllerScroll:
    return scroll_tool(speed), pan_tool()


def scroll_tool(speed: int = 10) -> Gtk.EventControllerScroll:
    """Scroll tool recognized 2 finger scroll gestures."""
    ctrl = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    ctrl.connect("scroll", on_scroll, speed)
    return ctrl


def on_scroll(controller, dx, dy, speed):
    view = controller.get_widget()

    modifiers = controller.get_current_event_state()

    if modifiers & Gdk.ModifierType.CONTROL_MASK:
        # Workaround: Gtk.EventController.get_current_event() causes SEGFAULT
        view = controller.get_widget()
        x = view.get_width() / 2
        y = view.get_height() / 2
        zoom = Zoom()
        zoom.begin(view.matrix, x, y)

        zoom_factor = 0.1
        d = 1 - dy * zoom_factor
        zoom.update(d)
    elif modifiers & Gdk.ModifierType.SHIFT_MASK:
        view.hadjustment.set_value(dy * speed - view.hadjustment.get_value())
        view.vadjustment.set_value(dx * speed - view.vadjustment.get_value())
    else:
        view.hadjustment.set_value(dx * speed - view.hadjustment.get_value())
        view.vadjustment.set_value(dy * speed - view.vadjustment.get_value())


class PanState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.h = 0
        self.v = 0


def pan_tool() -> Gtk.GestureDrag:
    gesture = Gtk.GestureDrag.new()
    gesture.set_button(Gdk.BUTTON_MIDDLE)
    pan_state = PanState()
    gesture.connect("drag-begin", on_drag_begin, pan_state)
    gesture.connect("drag-update", on_drag_update, pan_state)
    gesture.connect("drag-end", on_drag_end)
    return gesture


def on_drag_begin(gesture, start_x, start_y, pan_state):
    view = gesture.get_widget()
    pan_state.h = view.matrix[4]
    pan_state.v = view.matrix[5]
    set_cursor(view, "move")
    gesture.set_state(Gtk.EventSequenceState.CLAIMED)


def on_drag_update(gesture, offset_x, offset_y, pan_state):
    view = gesture.get_widget()
    view.matrix.set(x0=pan_state.h + offset_x, y0=pan_state.v + offset_y)
    set_cursor(view, "move")


def on_drag_end(gesture, _offset_x, _offset_y):
    view = gesture.get_widget()
    set_cursor(view, "default")
