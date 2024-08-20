from collections.abc import Collection

from cairo import Context as CairoContext
from gi.repository import Gtk

from gaphas.item import Item


class RubberbandState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.x0 = self.y0 = self.x1 = self.y1 = 0


class RubberbandPainter:
    """The rubberband painter should be used in conjunction with the rubberband
    tool.

    ``RubberbandState`` should be shared between the two.
    """

    def __init__(self, rubberband_state: RubberbandState) -> None:
        self.rubberband_state = rubberband_state

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        data = self.rubberband_state
        x0, y0, x1, y1 = data.x0, data.y0, data.x1, data.y1
        if x0 != x1 or y0 != y1:
            cairo.identity_matrix()
            cairo.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            cairo.set_source_rgba(0.9, 0.9, 0.9, 0.3)
            cairo.fill_preserve()
            cairo.set_line_width(2.0)
            cairo.set_dash((7.0, 5.0))
            cairo.set_source_rgba(0.5, 0.5, 0.7, 0.7)
            cairo.stroke()


def rubberband_tool(rubberband_state):
    """Rubberband selection tool.

    Should be used in conjunction with ``RubberbandPainter``.
    """
    gesture = Gtk.GestureDrag.new()
    gesture.connect("drag-begin", on_drag_begin, rubberband_state)
    gesture.connect("drag-update", on_drag_update, rubberband_state)
    gesture.connect("drag-end", on_drag_end, rubberband_state)
    return gesture


def on_drag_begin(gesture, start_x, start_y, rubberband_state):
    if gesture.set_state(Gtk.EventSequenceState.CLAIMED):
        rubberband_state.x0 = rubberband_state.x1 = start_x
        rubberband_state.y0 = rubberband_state.y1 = start_y


def on_drag_update(gesture, offset_x, offset_y, rubberband_state):
    rubberband_state.x1 = rubberband_state.x0 + offset_x
    rubberband_state.y1 = rubberband_state.y0 + offset_y
    view = gesture.get_widget()
    view.update_back_buffer()


def on_drag_end(gesture, offset_x, offset_y, rubberband_state):
    view = gesture.get_widget()
    x0 = rubberband_state.x0
    y0 = rubberband_state.y0
    x1 = x0 + offset_x
    y1 = y0 + offset_y
    items = view.get_items_in_rectangle(
        (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)), contain=True
    )
    view.selection.select_items(*items)
    rubberband_state.reset()
    view.update_back_buffer()
