from typing import Sequence

from gaphas.aspect import PaintFocused
from gaphas.item import Item


class FocusedItemPainter:
    """This painter allows for drawing on top of all the other layers for the
    focused item."""

    def __init__(self, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            view: (bool): write your description
        """
        assert view
        self.view = view

    def paint(self, items: Sequence[Item], cairo):
        """
        Paint the given item.

        Args:
            self: (todo): write your description
            items: (todo): write your description
            cairo: (todo): write your description
        """
        view = self.view
        item = view.selection.hovered_item
        if item and item is view.selection.focused_item:
            PaintFocused(item, view).paint(cairo)
