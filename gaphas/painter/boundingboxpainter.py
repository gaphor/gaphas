from __future__ import annotations

import functools
import operator
from typing import Collection, Dict

import cairo

from gaphas.geometry import Rectangle
from gaphas.item import Item
from gaphas.painter.painter import ItemPainterType
from gaphas.types import CairoContext


class BoundingBoxPainter:
    """This specific case of an ItemPainter is used to calculate the bounding
    boxes (in cairo device coordinates) for the items."""

    def __init__(
        self,
        item_painter: ItemPainterType,
    ):
        self.item_painter = item_painter

    def paint_item(self, item: Item, cr: CairoContext) -> Rectangle:
        surface = cairo.RecordingSurface(cairo.Content.COLOR_ALPHA, None)
        bbctx = cairo.Context(surface)
        self.item_painter.paint_item(item, bbctx)
        # Bounding box is in view (cairo root) coordinates
        bounds = Rectangle(*surface.ink_extents())

        # Update bounding box with handles.
        i2c = item.matrix_i2c.transform_point
        for h in item.handles():
            cx, cy = cr.user_to_device(*i2c(*h.pos))
            bounds += (cx - 5, cy - 5, 9, 9)

        bounds.expand(1)
        return bounds

    def paint(self, items: Collection[Item], cr: CairoContext) -> Dict[Item, Rectangle]:
        """Draw the items, return the bounding boxes (in cairo device
        coordinates)."""
        paint_item = self.paint_item
        boxes: Dict[Item, Rectangle] = {item: paint_item(item, cr) for item in items}
        return boxes

    def bounding_box(self, items: Collection[Item], cr: CairoContext) -> Rectangle:
        """Get the unified bounding box of the rendered items."""
        boxes = self.paint(items, cr)
        return functools.reduce(operator.add, boxes.values())
