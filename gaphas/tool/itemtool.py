import logging
from typing import Optional, Tuple, Union

from gi.repository import Gdk, Gtk
from typing_extensions import Protocol

from gaphas.aspect import HandleMove, Move, item_at_point
from gaphas.canvas import ancestors
from gaphas.connector import Handle
from gaphas.geometry import distance_point_point_fast
from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView

log = logging.getLogger(__name__)


class MoveType(Protocol):
    def __init__(self, item: Item, view: GtkView):
        ...

    def start_move(self, pos: Pos) -> None:
        ...

    def move(self, pos: Pos) -> None:
        ...

    def stop_move(self, pos: Pos) -> None:
        ...


def item_tool(view: GtkView) -> Gtk.GestureDrag:
    """Handle item movement and movement of handles."""
    gesture = (
        Gtk.GestureDrag.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.GestureDrag.new()
    )
    drag_state = DragState()
    gesture.connect("drag-begin", on_drag_begin, drag_state)
    gesture.connect("drag-update", on_drag_update, drag_state)
    gesture.connect("drag-end", on_drag_end, drag_state)
    return gesture


class DragState:
    def __init__(self):
        self.moving = set()


def on_drag_begin(gesture, start_x, start_y, drag_state):
    view = gesture.get_widget()
    selection = view.selection
    modifiers = (
        gesture.get_last_event(None).get_state()[1]
        if Gtk.get_major_version() == 3
        else gesture.get_current_event_state()
    )
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

    selection.focused_item = item
    gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    if handle:
        drag_state.moving = {HandleMove(item, handle, view)}
    else:
        drag_state.moving = set(moving_items(view))

    for moving in drag_state.moving:
        moving.start_move((start_x, start_y))


def find_item_and_handle_at_point(
    view: GtkView, pos: Pos
) -> Tuple[Optional[Item], Optional[Handle]]:
    item, handle = handle_at_point(view, pos)
    return item or item_at_point(view, pos), handle


def moving_items(view):
    """Filter the items that should eventually be moved.

    Returns Move aspects for the items.
    """
    selected_items = set(view.selection.selected_items)
    for item in selected_items:
        # Do not move subitems of selected items
        if not set(ancestors(view.model, item)).intersection(selected_items):
            yield Move(item, view)


def on_drag_update(gesture, offset_x, offset_y, drag_state):
    _, sx, sy = gesture.get_start_point()
    view = gesture.get_widget()
    allocation = view.get_allocation()
    x = sx + offset_x
    y = sy + offset_y

    for moving in drag_state.moving:
        moving.move((x, y))

    if not (0 <= x <= allocation.width and 0 <= y <= allocation.height):
        view.clamp_item(view.selection.focused_item)


def on_drag_end(gesture, offset_x, offset_y, drag_state):
    _, x, y = gesture.get_start_point()
    for moving in drag_state.moving:
        moving.stop_move((x + offset_x, y + offset_y))
    drag_state.moving = set()


def order_handles(handles):
    if handles:
        yield handles[0]
        yield handles[-1]
        yield from handles[1:-1]


def handle_at_point(
    view: GtkView, pos: Pos, distance: int = 6
) -> Union[Tuple[Item, Handle], Tuple[None, None]]:
    """Look for a handle at ``pos`` and return the tuple (item, handle)."""

    def find(item):
        """Find item's handle at pos."""
        v2i = view.get_matrix_v2i(item)
        d = distance_point_point_fast(v2i.transform_distance(0, distance))
        x, y = v2i.transform_point(*pos)

        for h in order_handles(item.handles()):
            if not h.movable:
                continue
            hx, hy = h.pos
            if -d < (hx - x) < d and -d < (hy - y) < d:
                return h

    selection = view.selection

    # The focused item is the preferred item for handle grabbing
    if selection.focused_item:
        h = find(selection.focused_item)
        if h:
            return selection.focused_item, h

    # then try hovered item
    if selection.hovered_item:
        h = find(selection.hovered_item)
        if h:
            return selection.hovered_item, h

    # Last try all items, checking the bounding box first
    x, y = pos
    items = reversed(
        list(
            view.get_items_in_rectangle(
                (x - distance, y - distance, distance * 2, distance * 2)
            )
        )
    )

    for item in items:
        h = find(item)
        if h:
            return item, h
    return None, None
