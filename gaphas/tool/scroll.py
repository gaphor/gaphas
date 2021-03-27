from gi.repository import Gtk

from gaphas.view import GtkView


def scroll_tool(view: GtkView, speed: int = 5) -> Gtk.EventControllerScroll:
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
    view.hadjustment.set_value(dx * speed - view.hadjustment.get_value())
    view.vadjustment.set_value(dy * speed - view.vadjustment.get_value())
