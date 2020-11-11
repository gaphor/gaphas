from functools import singledispatch

from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView


class ItemHandleFinder:
    """Deals with the task of finding handles."""

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos: Pos):
        return self.view.get_handle_at_point(pos)


HandleFinder = singledispatch(ItemHandleFinder)
