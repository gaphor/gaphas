import logging
from typing import Optional, Tuple, Union

from gi.repository import Gdk, Gtk
from typing_extensions import Protocol

from gaphas.aspect import HandleMove, Move
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
    gesture = Gtk.GestureDrag.new(view)
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
    _, x, y = gesture.get_start_point()
    for moving in drag_state.moving:
        moving.move((x + offset_x, y + offset_y))


def on_drag_end(gesture, offset_x, offset_y, drag_state):
    _, x, y = gesture.get_start_point()
    for moving in drag_state.moving:
        moving.stop_move((x + offset_x, y + offset_y))
    drag_state.moving = set()


def item_at_point(view: GtkView, pos: Pos, selected: bool = True) -> Optional[Item]:
    """Return the topmost item located at ``pos`` (x, y).

    Parameters:
        - view: a view
        - pos: Position, a tuple ``(x, y)`` in view coordinates
        - selected: if False returns first non-selected item
    """
    item: Item
    for item in reversed(list(view.get_items_in_rectangle((pos[0], pos[1], 1, 1)))):
        if not selected and item in view.selection.selected_items:
            continue  # skip selected items

        v2i = view.get_matrix_v2i(item)
        ix, iy = v2i.transform_point(*pos)
        item_distance = item.point(ix, iy)
        if item_distance is None:
            log.warning("Item distance is None for %s", item)
            continue
        if item_distance < 0.5:
            return item
    return None


def handle_at_point(
    view: GtkView, pos: Pos, distance: int = 6
) -> Union[Tuple[Item, Handle], Tuple[None, None]]:
    """Look for a handle at ``pos`` and return the tuple (item, handle)."""

    def find(item):
        """Find item's handle at pos."""
        v2i = view.get_matrix_v2i(item)
        d = distance_point_point_fast(v2i.transform_distance(0, distance))
        x, y = v2i.transform_point(*pos)

        for h in item.handles():
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
