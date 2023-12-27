from __future__ import annotations

from gi.repository import Gdk, Gtk


class Zoom:
    def __init__(self):
        self.matrix = None
        self.x0 = 0
        self.y0 = 0
        self.sx = 1.0
        self.sy = 1.0

    def begin(self, matrix, x0, y0):
        self.matrix = matrix
        self.x0 = x0
        self.y0 = y0
        self.sx = matrix[0]
        self.sy = matrix[3]

    def update(self, scale):
        assert self.matrix
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


def zoom_tools() -> (
    tuple[Gtk.GestureZoom] | tuple[Gtk.GestureZoom, Gtk.EventControllerScroll]
):
    return zoom_tool(), scroll_zoom_tool()


def zoom_tool() -> Gtk.GestureZoom:
    """Create a zoom tool as a Gtk.Gesture.

    Note: we need to keep a reference to this gesture, or else it will be destroyed.
    """
    zoom = Zoom()
    gesture = Gtk.GestureZoom.new()
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    gesture.connect("begin", on_begin, zoom)
    gesture.connect("scale-changed", on_scale_changed, zoom)
    return gesture


def on_begin(
    gesture: Gtk.GestureZoom,
    sequence: None,
    zoom: Zoom,
) -> None:
    view = gesture.get_widget()
    _, x0, y0 = gesture.get_point(sequence)
    zoom.begin(view.matrix, x0, y0)


def on_scale_changed(_gesture: Gtk.GestureZoom, scale: float, zoom: Zoom) -> None:
    zoom.update(scale)


def scroll_zoom_tool() -> Gtk.EventControllerScroll:
    """Ctrl-scroll wheel zoom."""
    ctrl = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    ctrl.connect("scroll", on_scroll)
    return ctrl


def on_scroll(controller, _dx, dy):
    view = controller.get_widget()

    modifiers = controller.get_current_event_state()

    if not modifiers & Gdk.ModifierType.CONTROL_MASK:
        return False

    # Workaround: Gtk.EventController.get_current_event() causes SEGFAULT
    view = controller.get_widget()
    x = view.get_width() / 2
    y = view.get_height() / 2
    zoom = Zoom()
    zoom.begin(view.matrix, x, y)

    zoom_factor = 0.1
    d = 1 - dy * zoom_factor
    zoom.update(d)
    return True
