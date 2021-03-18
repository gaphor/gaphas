from __future__ import annotations

from typing import Collection

import cairo

from gaphas.geometry import Rectangle
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

    def bounding_box(self, items: Collection[Item], cr: CairoContext) -> Rectangle:
        """Get the unified bounding box of the rendered items."""
        surface = cairo.RecordingSurface(cairo.Content.COLOR_ALPHA, None)  # type: ignore[arg-type]
        cr = cairo.Context(surface)
        self.paint(items, cr)
        return Rectangle(*surface.ink_extents())
