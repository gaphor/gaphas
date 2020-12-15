from typing import Collection, Optional

from cairo import LINE_JOIN_ROUND

from gaphas.item import DrawContext, Item
from gaphas.types import CairoContext
from gaphas.view.selection import Selection

# The tolerance for Cairo. Bigger values increase speed and reduce accuracy
# (default: 0.1)
TOLERANCE = 0.8


class ItemPainter:

    draw_all = False

    def __init__(self, selection: Optional[Selection] = None) -> None:
        self.selection = selection or Selection()

    def paint_item(self, item: Item, cairo: CairoContext) -> None:
        cairo.save()
        try:
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
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)

        for item in items:
            self.paint_item(item, cairo)
