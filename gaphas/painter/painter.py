"""The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes care of a layer in the canvas (such as grid, items
and handles).
"""

from typing import Collection

from typing_extensions import Protocol

from gaphas.item import Item
from gaphas.types import CairoContext


class Painter(Protocol):
    """Painter interface."""

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        """Do the paint action (called from the View)."""
        pass


class ItemPainterType(Protocol):
    def paint_item(self, item: Item, cairo: CairoContext) -> None:
        """Draw a single item."""

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        """Do the paint action (called from the View)."""
        pass
