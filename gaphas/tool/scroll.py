from gi.repository import Gtk

from gaphas.view import GtkView


def scroll_tool(view: GtkView, speed=5):
    ctrl = Gtk.EventControllerScroll.new(
        view, Gtk.EventControllerScrollFlags.BOTH_AXES,
    )
    ctrl.connect("scroll", on_scroll, speed)
    return ctrl


def on_scroll(controller, dx, dy, speed):
    view = controller.get_widget()
    m = view.matrix
    m.translate(-dx * speed, -dy * speed)
    view.request_update((), view.canvas.get_all_items())
