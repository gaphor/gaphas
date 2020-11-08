from typing import Collection, Optional

from cairo import LINE_JOIN_ROUND

from gaphas.canvas import Context
from gaphas.item import Item
from gaphas.view.selection import Selection

# The tolerance for Cairo. Bigger values increase speed and reduce accuracy
# (default: 0.1)
TOLERANCE = 0.8


class DrawContext(Context):
    """Special context for draw()'ing the item.

    The draw-context contains stuff like the cairo context and
    properties like selected and focused.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ItemPainter:

    draw_all = False

    def __init__(self, selection: Optional[Selection] = None):
        self.selection = selection or Selection()

    def paint_item(self, item, cairo):
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
                    dropzone=(item is selection.dropzone_item),
                )
            )

        finally:
            cairo.restore()

    def paint(self, items: Collection[Item], cairo):
        """Draw the items."""
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)

        for item in items:
            self.paint_item(item, cairo)
