from functools import singledispatch
from typing import Tuple, Union

from gaphas.connector import Handle
from gaphas.geometry import distance_point_point_fast
from gaphas.item import Item
from gaphas.types import Pos


class ItemFinder:
    """Find an item on the canvas."""

    def __init__(self, view):
        self.view = view

    def get_item_at_point(self, pos: Pos):
        item, handle = handle_at_point(self.view, pos)
        return item or self.view.get_item_at_point(pos)


Finder = singledispatch(ItemFinder)


def handle_at_point(
    view, pos, distance=6
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
