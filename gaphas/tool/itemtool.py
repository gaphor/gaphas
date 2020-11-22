from gi.repository import Gdk, Gtk
from typing_extensions import Protocol

from gaphas.aspect import HandleMove, Move
from gaphas.aspect.finder import handle_at_point, item_at_point
from gaphas.canvas import ancestors
from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView

# Handle click/move/release in one or more event handlers, like rubberband and handle tool


class MoveType(Protocol):
    def __init__(self, item: Item, view: GtkView):
        ...

    def start_move(self, pos: Pos):
        ...

    def move(self, pos: Pos):
        ...

    def stop_move(self, pos: Pos):
        ...


class DragState:
    def __init__(self):
        self.moving = set()


def on_drag_begin(gesture, start_x, start_y, view, drag_state):
    selection = view.selection
    event = gesture.get_last_event(None)
    modifiers = event.get_state()[1]
    item, handle = find_item_and_handle_at_point(view, (start_x, start_y))

    # Deselect all items unless CTRL or SHIFT is pressed
    # or the item is already selected.
    if not (
        modifiers & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
        or item in selection.selected_items
    ):
        selection.unselect_all()

    if not item:
        gesture.set_state(Gtk.EventSequenceState.DENIED)
        return

    if (
        not handle
        and item in selection.selected_items
        and modifiers & Gdk.ModifierType.CONTROL_MASK
    ):
        selection.unselect_item(item)
        gesture.set_state(Gtk.EventSequenceState.DENIED)
        return

    selection.set_focused_item(item)

    if handle:
        drag_state.moving = {HandleMove(item, handle, view)}
    else:
        drag_state.moving = set(moving_items(view))

    for moving in drag_state.moving:
        moving.start_move((start_x, start_y))


def find_item_and_handle_at_point(view: GtkView, pos: Pos):
    item, handle = handle_at_point(view, pos)
    return item or item_at_point(view, pos), handle


def moving_items(view):
    """Filter the items that should eventually be moved.

    Returns Move aspects for the items.
    """
    selected_items = set(view.selection.selected_items)
    for item in selected_items:
        # Do not move subitems of selected items
        if not set(ancestors(view.canvas, item)).intersection(selected_items):
            yield Move(item, view)


def on_drag_update(gesture, offset_x, offset_y, view, drag_state):
    _, x, y = gesture.get_start_point()
    for moving in drag_state.moving:
        moving.move((x + offset_x, y + offset_y))


def on_drag_end(gesture, offset_x, offset_y, view, drag_state):
    _, x, y = gesture.get_start_point()
    for moving in drag_state.moving:
        moving.stop_move((x + offset_x, y + offset_y))
    drag_state.moving = set()


def item_tool(view):
    gesture = Gtk.GestureDrag.new(view)
    drag_state = DragState()
    gesture.connect("drag-begin", on_drag_begin, view, drag_state)
    gesture.connect("drag-update", on_drag_update, view, drag_state)
    gesture.connect("drag-end", on_drag_end, view, drag_state)
    return gesture
