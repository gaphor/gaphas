from functools import singledispatch

from gaphas.item import Item
from gaphas.view import Selection


class ItemSelector:
    """A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @aspect decorator to a
    subclass.
    """

    def __init__(self, item: Item, selection: Selection):
        self.item = item
        self.selection = selection

    def select(self):
        """Set selection on the view."""
        self.selection.set_focused_item(self.item)

    def unselect(self):
        self.selection.unselect_item(self.item)


Selector = singledispatch(ItemSelector)
