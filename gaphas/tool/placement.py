from __future__ import annotations

from collections.abc import Callable

from gi.repository import Gtk

from gaphas.handlemove import HandleMove
from gaphas.item import Item
from gaphas.move import MoveType

FactoryType = Callable[[], Item]


def placement_tool(factory: FactoryType, handle_index: int) -> Gtk.GestureDrag:
    """Place a new item on the model."""
    gesture = Gtk.GestureDrag.new()
    placement_state = PlacementState(factory, handle_index)
    gesture.connect("drag-begin", on_drag_begin, placement_state)
    gesture.connect("drag-update", on_drag_update, placement_state)
    gesture.connect("drag-end", on_drag_end, placement_state)
    return gesture


class PlacementState:
    def __init__(self, factory: FactoryType, handle_index: int):
        self.factory = factory
        self.handle_index = handle_index
        self.moving: MoveType | None = None
        self.start_x = 0
        self.start_y = 0


def on_drag_begin(gesture, start_x, start_y, placement_state):
    view = gesture.get_widget()
    item = placement_state.factory()
    x, y = view.get_matrix_v2i(item).transform_point(start_x, start_y)
    item.matrix.translate(x, y)
    view.selection.unselect_all()
    view.selection.focused_item = item

    gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    handle = item.handles()[placement_state.handle_index]
    if handle.movable:
        placement_state.start_x = start_x
        placement_state.start_y = start_y
        placement_state.moving = HandleMove(item, handle, view)
        placement_state.moving.start_move((start_x, start_y))


def on_drag_update(gesture, offset_x, offset_y, placement_state):
    if placement_state.moving:
        placement_state.moving.move(
            (placement_state.start_x + offset_x, placement_state.start_y + offset_y)
        )


def on_drag_end(gesture, offset_x, offset_y, placement_state):
    if placement_state.moving:
        placement_state.moving.stop_move(
            (placement_state.start_x + offset_x, placement_state.start_y + offset_y)
        )
