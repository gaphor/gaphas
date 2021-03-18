from gi.repository import Gtk

from gaphas.view import GtkView


class ZoomData:
    x0: int
    y0: int
    sx: float
    sy: float


def zoom_tool(view: GtkView) -> Gtk.GestureZoom:
    """Create a zoom tool as a Gtk.Gesture.

    Note: we need to keep a reference to this gesture, or else it will be destroyed.
    """
    zoom_data = ZoomData()
    gesture = (
        Gtk.GestureZoom.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.GestureZoom.new()
    )
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    gesture.connect("begin", on_begin, zoom_data)
    gesture.connect("scale-changed", on_scale_changed, zoom_data)
    return gesture


def on_begin(
    gesture: Gtk.GestureZoom,
    sequence: None,
    zoom_data: ZoomData,
) -> None:
    _, zoom_data.x0, zoom_data.y0 = gesture.get_point(sequence)
    view = gesture.get_widget()
    zoom_data.sx = view.matrix[0]
    zoom_data.sy = view.matrix[3]


def on_scale_changed(
    gesture: Gtk.GestureZoom, scale: float, zoom_data: ZoomData
) -> None:
    if zoom_data.sx * scale < 0.2:
        scale = 0.2 / zoom_data.sx
    elif zoom_data.sx * scale > 20.0:
        scale = 20.0 / zoom_data.sx

    view = gesture.get_widget()
    m = view.matrix
    sx = m[0]
    sy = m[3]
    ox = (m[4] - zoom_data.x0) / sx
    oy = (m[5] - zoom_data.y0) / sy
    dsx = zoom_data.sx * scale / sx
    dsy = zoom_data.sy * scale / sy
    m.translate(-ox, -oy)
    m.scale(dsx, dsy)
    m.translate(+ox, +oy)
