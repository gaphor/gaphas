from gi.repository import Gdk, Gtk

from gaphas.view import GtkView


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
    zoom_factor = 0.1
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
            x = view.get_width() / 2
            y = view.get_height() / 2
        d = 1 - dy * zoom_factor
        m = view.matrix
        sx = m[0]
        sy = m[3]
        ox = (m[4] - x) / sx
        oy = (m[5] - y) / sy
        m.translate(-ox, -oy)
        m.scale(d, d)
        m.translate(+ox, +oy)
    else:
        view.hadjustment.set_value(dx * speed - view.hadjustment.get_value())
        view.vadjustment.set_value(dy * speed - view.vadjustment.get_value())
