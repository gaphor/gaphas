from __future__ import annotations

import functools
import operator
from typing import Collection, Dict, Optional

from gaphas.geometry import Rectangle
from gaphas.item import Item
from gaphas.painter.painter import ItemPainterType
from gaphas.types import CairoContext


class CairoBoundingBoxContext:
    """Delegate all calls to the wrapped CairoBoundingBoxContext, intercept
    ``stroke()``, ``fill()`` and a few others so the bounding box of the item
    involved can be calculated."""

    def __init__(self, cr):
        self.cr = cr
        self._bounds: Optional[Rectangle] = None  # a Rectangle object

    def __getattr__(self, key):
        return getattr(self.cr, key)

    def get_bounds(self) -> Rectangle:
        """Return the bounding box."""
        return self._bounds or Rectangle()

    def _update_bounds(self, bounds):
        if bounds:
            if not self._bounds:
                self._bounds = bounds
            else:
                self._bounds += bounds

    def _extents(self, extents_func, line_width=False):
        """Calculate the bounding box for a given drawing operation.

        if ``line_width`` is True, the current line-width is taken into
        account.
        """
        cr = self.cr
        cr.save()
        cr.identity_matrix()
        x0, y0, x1, y1 = extents_func()
        b = Rectangle(x0, y0, x1=x1, y1=y1)
        cr.restore()
        if b and line_width:
            # Do this after the restore(), so we can get the proper width.
            lw = cr.get_line_width() / 2
            d = cr.user_to_device_distance(lw, lw)
            b.expand(d[0] + d[1])
        self._update_bounds(b)
        return b

    def fill(self, b=None):
        """Interceptor for Cairo drawing method."""
        cr = self.cr
        if not b:
            b = self._extents(cr.fill_extents)
        cr.fill()

    def fill_preserve(self, b=None):
        """Interceptor for Cairo drawing method."""
        if not b:
            cr = self.cr
            b = self._extents(cr.fill_extents)

    def stroke(self, b=None):
        """Interceptor for Cairo drawing method."""
        cr = self.cr
        if not b:
            b = self._extents(cr.stroke_extents, line_width=True)
        cr.stroke()

    def stroke_preserve(self, b=None):
        """Interceptor for Cairo drawing method."""
        if not b:
            cr = self.cr
            b = self._extents(cr.stroke_extents, line_width=True)

    def show_text(self, utf8, b=None):
        """Interceptor for Cairo drawing method."""
        cr = self.cr
        if not b:
            x, y = cr.get_current_point()
            e = cr.text_extents(utf8)
            x0, y0 = cr.user_to_device(x + e[0], y + e[1])
            x1, y1 = cr.user_to_device(x + e[0] + e[2], y + e[1] + e[3])
            b = Rectangle(x0, y0, x1=x1, y1=y1)
            self._update_bounds(b)
        cr.show_text(utf8)


class BoundingBoxPainter:
    """This specific case of an ItemPainter is used to calculate the bounding
    boxes (in cairo device coordinates) for the items."""

    draw_all = True

    def __init__(
        self, item_painter: ItemPainterType,
    ):
        self.item_painter = item_painter

    def paint_item(self, item: Item, cairo: CairoContext) -> Rectangle:
        bbctx = CairoBoundingBoxContext(cairo)
        self.item_painter.paint_item(item, bbctx)
        # Bounding box is in view (cairo root) coordinates
        bounds = bbctx.get_bounds()

        # Update bounding box with handles.
        i2c = item.matrix_i2c.transform_point
        for h in item.handles():
            cx, cy = cairo.user_to_device(*i2c(*h.pos))
            bounds += (cx - 5, cy - 5, 9, 9)

        bounds.expand(1)
        return bounds

    def paint(
        self, items: Collection[Item], cairo: CairoContext
    ) -> Dict[Item, Rectangle]:
        """Draw the items, return the bounding boxes (in cairo device
        coordinates)."""
        paint_item = self.paint_item
        boxes: Dict[Item, Rectangle] = {item: paint_item(item, cairo) for item in items}
        return boxes

    def bounding_box(self, items: Collection[Item], cairo: CairoContext) -> Rectangle:
        """Get the unified bounding box of the rendered items."""
        boxes = self.paint(items, cairo)
        return functools.reduce(operator.add, boxes.values())
