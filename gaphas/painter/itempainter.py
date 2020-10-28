from typing import Optional, Sequence

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
        self.selection = selection

    def paint_item(self, item, cairo):
        cairo.save()
        try:
            cairo.transform(item.matrix_i2c.to_cairo())

            selection = self.selection
            if not selection:
                selection = Selection()
            item.draw(
                DrawContext(
                    painter=self,
                    cairo=cairo,
                    _item=item,
                    selected=(item in selection.selected_items),
                    focused=(item is selection.focused_item),
                    hovered=(item is selection.hovered_item),
                    dropzone=(item is selection.dropzone_item),
                    draw_all=self.draw_all,
                )
            )

        finally:
            cairo.restore()

    def paint(self, items: Sequence[Item], cairo):
        """Draw the items."""
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)

        for item in items:
            self.paint_item(item, cairo)
