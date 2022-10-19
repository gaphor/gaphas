from __future__ import annotations

from gi.repository import Gdk, Gtk

from gaphas.view import GtkView


class Zoom:
    def __init__(self, matrix):
        self.matrix = matrix
        self.x0 = 0
        self.y0 = 0
        self.sx = 1.0
        self.sy = 1.0

    def begin(self, x0, y0):
        self.x0 = x0
        self.y0 = y0
        self.sx = self.matrix[0]
        self.sy = self.matrix[3]

    def update(self, scale):
        if self.sx * scale < 0.2:
            scale = 0.2 / self.sx
        elif self.sx * scale > 20.0:
            scale = 20.0 / self.sx

        m = self.matrix
        sx = m[0]
        sy = m[3]
        ox = (m[4] - self.x0) / sx
        oy = (m[5] - self.y0) / sy
        dsx = self.sx * scale / sx
        dsy = self.sy * scale / sy
        m.translate(-ox, -oy)
        m.scale(dsx, dsy)
        m.translate(+ox, +oy)


def zoom_tools(
    view: GtkView,
) -> tuple[Gtk.GestureZoom] | tuple[Gtk.GestureZoom, Gtk.EventControllerScroll]:
    return (
        (zoom_tool(view),)
        if Gtk.get_major_version() == 3
        else (zoom_tool(view), scroll_zoom_tool(view))
    )


def zoom_tool(view: GtkView) -> Gtk.GestureZoom:
    """Create a zoom tool as a Gtk.Gesture.

    Note: we need to keep a reference to this gesture, or else it will be destroyed.
    """
    zoom = Zoom(view.matrix)
    gesture = (
        Gtk.GestureZoom.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.GestureZoom.new()
    )
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    gesture.connect("begin", on_begin, zoom)
    gesture.connect("scale-changed", on_scale_changed, zoom)
    return gesture


def on_begin(
    gesture: Gtk.GestureZoom,
    sequence: None,
    zoom: Zoom,
) -> None:
    _, x0, y0 = gesture.get_point(sequence)
    zoom.begin(x0, y0)


def on_scale_changed(gesture: Gtk.GestureZoom, scale: float, zoom: Zoom) -> None:
    zoom.update(scale)


def scroll_zoom_tool(view: GtkView) -> Gtk.EventControllerScroll:
    """Ctrl-scroll wheel zoom.

    GTK4 only.
    """
    ctrl = (
        Gtk.EventControllerScroll.new(
            view,
            Gtk.EventControllerScrollFlags.BOTH_AXES,
        )
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    )
    ctrl.connect("scroll", on_scroll)
    return ctrl


def on_scroll(controller, _dx, dy):
    view = controller.get_widget()

    modifiers = (
        Gtk.get_current_event_state()[1]
        if Gtk.get_major_version() == 3
        else controller.get_current_event_state()
    )

    if not modifiers & Gdk.ModifierType.CONTROL_MASK:
        return False

    # Workaround: Gtk.EventController.get_current_event() causes SEGFAULT
    view = controller.get_widget()
    x = view.get_width() / 2
    y = view.get_height() / 2
    zoom = Zoom(view.matrix)
    zoom.begin(x, y)

    zoom_factor = 0.1
    d = 1 - dy * zoom_factor
    zoom.update(d)
    return True
