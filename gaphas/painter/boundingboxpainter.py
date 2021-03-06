from __future__ import annotations

from typing import Collection

from gaphas.item import Item
from gaphas.painter.painter import ItemPainterType
from gaphas.types import CairoContext


class BoundingBoxPainter:
    """This specific case of an ItemPainter is used to calculate the bounding
    boxes (in cairo device coordinates) for the items.

    Deprecated since 3.2: Bounding boxes are calculated in the View
    directly. This class is not a pass-through for the provided
    item_painter.
    """

    def __init__(
        self,
        item_painter: ItemPainterType,
    ):
        self.item_painter = item_painter

    def paint_item(self, item: Item, cr: CairoContext) -> None:
        self.item_painter.paint_item(item, cr)

    def paint(self, items: Collection[Item], cr: CairoContext) -> None:
        """Draw the items, return the bounding boxes (in cairo device
        coordinates)."""
        self.item_painter.paint(items, cr)
