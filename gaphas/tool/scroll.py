from gi.repository import Gdk, Gtk

from gaphas.tool.zoom import Zoom
from gaphas.view import GtkView


def scroll_tools(view: GtkView, speed: int = 10) -> Gtk.EventControllerScroll:
    return scroll_tool(view, speed), pan_tool(view)


def scroll_tool(view: GtkView, speed: int = 10) -> Gtk.EventControllerScroll:
    """Scroll tool recognized 2 finger scroll gestures."""
    ctrl = (
        Gtk.EventControllerScroll.new(
            view,
            Gtk.EventControllerScrollFlags.BOTH_AXES,
        )
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    )
    ctrl.connect("scroll", on_scroll, speed)
    return ctrl


def on_scroll(controller, dx, dy, speed):
    view = controller.get_widget()

    modifiers = (
        Gtk.get_current_event_state()[1]
        if Gtk.get_major_version() == 3
        else controller.get_current_event_state()
    )

    if modifiers & Gdk.ModifierType.CONTROL_MASK:
        if Gtk.get_major_version() == 3:
            event = Gtk.get_current_event()
            x = event.x
            y = event.y
        else:
            # Workaround: Gtk.EventController.get_current_event() causes SEGFAULT
            view = controller.get_widget()
            x = view.get_width() / 2
            y = view.get_height() / 2
        zoom = Zoom(view.matrix)
        zoom.begin(x, y)

        zoom_factor = 0.1
        d = 1 - dy * zoom_factor
        zoom.update(d)
    else:
        view.hadjustment.set_value(dx * speed - view.hadjustment.get_value())
        view.vadjustment.set_value(dy * speed - view.vadjustment.get_value())


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
