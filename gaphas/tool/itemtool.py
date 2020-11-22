from gi.repository import Gdk, Gtk
from typing_extensions import Protocol

from gaphas.aspect import Move
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

    def stop_move(self):
        ...


class DragState:
    def __init__(self):
        self.moving_items = set()
        self.moving_item = None
        self.moving_handle = None


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

    if handle:
        drag_state.moving_handle = handle
        drag_state.moving_item = item
    if item:
        if (
            selection.hovered_item in selection.selected_items
            and modifiers & Gdk.ModifierType.CONTROL_MASK
        ):
            selection.unselect_item(item)
        else:
            selection.set_focused_item(item)


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
    if not drag_state.moving_items:
        drag_state.moving_items = set(moving_items(view))
        for moving in drag_state.moving_items:
            moving.start_move((offset_x, offset_y))
    else:
        for moving in drag_state.moving_items:
            moving.move((offset_x, offset_y))


def on_drag_end(gesture, offset_x, offset_y, view, drag_state):
    for moving in drag_state.moving_items:
        moving.stop_move()
    drag_state.moving_items.clear()


def item_tool(view):
    gesture = Gtk.GestureDrag.new(view)
    drag_state = DragState()
    gesture.connect("drag-begin", on_drag_begin, view)
    gesture.connect("drag-update", on_drag_update, view, drag_state)
    gesture.connect("drag-end", on_drag_end, view, drag_state)
    return gesture
