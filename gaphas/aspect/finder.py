from functools import singledispatch

from gaphas.types import Pos


class ItemFinder:
    """Find an item on the canvas."""

    def __init__(self, view):
        self.view = view

    def get_item_at_point(self, pos: Pos):
        item, handle = self.view.get_handle_at_point(pos)
        return item or self.view.get_item_at_point(pos)


Finder = singledispatch(ItemFinder)
