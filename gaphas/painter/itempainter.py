from cairo import LINE_JOIN_ROUND

from gaphas.canvas import Context

DEBUG_DRAW_BOUNDING_BOX = False

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

    def __init__(self, view):
        assert view
        self.view = view

    def draw_item(self, item, cairo):
        view = self.view
        cairo.save()
        try:
            cairo.set_matrix(view.matrix.to_cairo())
            cairo.transform(view.canvas.get_matrix_i2c(item).to_cairo())

            item.draw(
                DrawContext(
                    painter=self,
                    cairo=cairo,
                    _item=item,
                    selected=(item in view.selection.selected_items),
                    focused=(item is view.selection.focused_item),
                    hovered=(item is view.selection.hovered_item),
                    dropzone=(item is view.selection.dropzone_item),
                    draw_all=self.draw_all,
                )
            )

        finally:
            cairo.restore()

    def draw_items(self, items, cairo):
        """Draw the items."""
        for item in items:
            self.draw_item(item, cairo)
            if DEBUG_DRAW_BOUNDING_BOX:
                self._draw_bounds(item, cairo)

    def _draw_bounds(self, item, cairo):
        view = self.view
        try:
            b = view.get_item_bounding_box(item)
        except KeyError:
            pass  # No bounding box right now..
        else:
            cairo.save()
            cairo.identity_matrix()
            cairo.set_source_rgb(0.8, 0, 0)
            cairo.set_line_width(1.0)
            cairo.rectangle(*b)
            cairo.stroke()
            cairo.restore()

    def paint(self, context):
        cairo = context.cairo
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)
        self.draw_items(context.items, cairo)
