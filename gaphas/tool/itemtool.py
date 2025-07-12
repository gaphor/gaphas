from __future__ import annotations

import logging
from typing import Callable, Union

from gi.repository import Gdk, Gtk

from gaphas.canvas import ancestors
from gaphas.connector import Handle
from gaphas.geometry import distance_line_point, distance_point_point_fast
from gaphas.handlemove import HandleMove, item_at_point
from gaphas.item import Item
from gaphas.move import Move
from gaphas.segment import Segment
from gaphas.types import Pos
from gaphas.view import GtkView

log = logging.getLogger(__name__)


def default_find_item_and_handle_at_point(
    view: GtkView, pos: Pos
) -> Union[tuple[Item, Union[Handle, None]], tuple[None, None]]:
    item, handle = handle_at_point(view, pos)
    return item or next(item_at_point(view, pos), None), handle  # type: ignore[return-value]


def item_tool(
    find_item_and_handle_at_point: Callable[
        [GtkView, Pos], tuple[Item, Handle | None] | tuple[None, None]
    ] = default_find_item_and_handle_at_point,
) -> Gtk.GestureDrag:
    """Handle item movement and movement of handles."""
    gesture = Gtk.GestureDrag.new()
    drag_state = DragState()
    gesture.connect(
        "drag-begin", on_drag_begin, drag_state, find_item_and_handle_at_point
    )
    gesture.connect("drag-update", on_drag_update, drag_state)
    gesture.connect("drag-end", on_drag_end, drag_state)
    return gesture


class DragState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.moving_items = set()
        self.moving_handle = None
        self.start_x = 0
        self.start_y = 0

    @property
    def moving(self):
        yield from self.moving_items
        if self.moving_handle:
            yield self.moving_handle


def on_drag_begin(gesture, start_x, start_y, drag_state, find_item_and_handle_at_point):
    view = gesture.get_widget()
    pos = (start_x, start_y)
    selection = view.selection
    modifiers = gesture.get_current_event_state()
    item, handle = find_item_and_handle_at_point(view, pos)

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

    if not handle and item is view.selection.focused_item:
        handle = maybe_split_segment(view, item, pos)

    selection.focused_item = item
    gesture.set_state(Gtk.EventSequenceState.CLAIMED)

    drag_state.start_x = start_x
    drag_state.start_y = start_y

    if handle:
        drag_state.moving_handle = HandleMove(item, handle, view)
    else:
        drag_state.moving_items = set(moving_items(view))

    for moving in drag_state.moving:
        moving.start_move((start_x, start_y))


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
    view = gesture.get_widget()
    x = drag_state.start_x + offset_x
    y = drag_state.start_y + offset_y

    for moving in drag_state.moving:
        moving.move((x, y))

    if not (0 <= x <= view.get_width() and 0 <= y <= view.get_height()):
        view.clamp_item(view.selection.focused_item)


def on_drag_end(gesture, offset_x, offset_y, drag_state):
    for moving in drag_state.moving:
        moving.stop_move((drag_state.start_x + offset_x, drag_state.start_y + offset_y))
    if drag_state.moving_handle:
        moving = drag_state.moving_handle
        maybe_merge_segments(gesture.get_widget(), moving.item, moving.handle)
    drag_state.reset()


def order_handles(handles):
    if handles:
        yield handles[0]
        yield handles[-1]
        yield from handles[1:-1]


def handle_at_point(
    view: GtkView, pos: Pos, distance: int = 6
) -> tuple[Item, Handle] | tuple[None, None]:
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


def maybe_split_segment(view, item, pos):
    try:
        segment = Segment(item, view.model)
    except TypeError:
        return None
    else:
        cpos = view.matrix.inverse().transform_point(*pos)
        return segment.split(cpos)


def maybe_merge_segments(view, item, handle):
    handles = item.handles()

    # don't merge using first or last handle
    if handles[0] is handle or handles[-1] is handle:
        return

    # ensure at least three handles
    handle_index = handles.index(handle)
    segment = handle_index - 1

    # cannot merge starting from last segment
    if segment == len(item.ports()) - 1:
        segment = -1
    assert segment >= 0 and segment < len(item.ports()) - 1

    before = handles[handle_index - 1]
    after = handles[handle_index + 1]
    d, p = distance_line_point(before.pos, after.pos, handle.pos)

    if d > 4:
        return

    try:
        Segment(item, view.model).merge_segment(segment)
    except ValueError:
        pass
    else:
        if handle:
            view.model.request_update(item)
