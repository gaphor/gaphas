from functools import singledispatch

from gaphas.aspect.finder import handle_at_point
from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView

# Used by Segment code


class ItemHandleFinder:
    """Deals with the task of finding handles."""

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos: Pos):
        return handle_at_point(self.view, pos)


HandleFinder = singledispatch(ItemHandleFinder)
