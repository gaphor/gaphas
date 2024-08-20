from __future__ import annotations

from collections.abc import Collection

from cairo import LINE_JOIN_ROUND
from cairo import Context as CairoContext

from gaphas.item import DrawContext, Item
from gaphas.selection import Selection


class ItemPainter:
    def __init__(self, selection: Selection | None = None) -> None:
        self.selection = selection or Selection()

    def paint_item(self, item: Item, cairo: CairoContext) -> None:
        cairo.save()
        try:
            cairo.set_line_join(LINE_JOIN_ROUND)
            cairo.transform(item.matrix_i2c.to_cairo())

            selection = self.selection
            item.draw(
                DrawContext(
                    cairo=cairo,
                    selected=(item in selection.selected_items),
                    focused=(item is selection.focused_item),
                    hovered=(item is selection.hovered_item),
                )
            )

        finally:
            cairo.restore()

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        """Draw the items."""

        for item in items:
            self.paint_item(item, cairo)
