from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING, Collection

from gaphas.item import Item

if TYPE_CHECKING:
    from gaphas.view import GtkView


class ItemPaintFocused:
    """Paints on top of all items, just for the focused item and only when it's
    hovered (see gaphas.painter.FocusedItemPainter)"""

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def paint(self, cairo):
        pass


PaintFocused = singledispatch(ItemPaintFocused)


class FocusedItemPainter:
    """This painter allows for drawing on top of all the other layers for the
    focused item."""

    def __init__(self, view):
        assert view
        self.view = view

    def paint(self, items: Collection[Item], cairo):
        view = self.view
        item = view.selection.hovered_item
        if item and item is view.selection.focused_item:
            PaintFocused(item, view).paint(cairo)
