from cairo import ANTIALIAS_NONE

from gaphas.painter.painter import Painter


class HandlePainter(Painter):
    """Draw handles of items that are marked as selected in the view."""

    def _draw_handles(self, item, cairo, opacity=None, inner=False):
        """Draw handles for an item.

        The handles are drawn in non-antialiased mode for clarity.
        """
        view = self.view
        cairo.save()
        i2v = view.get_matrix_i2v(item)
        if not opacity:
            opacity = (item is view.selection.focused_item) and 0.7 or 0.4

        cairo.set_line_width(1)

        get_connection = view.canvas.get_connection
        for h in item.handles():
            if not h.visible:
                continue
            # connected and not being moved, see HandleTool.on_button_press
            if get_connection(h):
                r, g, b = 1.0, 0.0, 0.0
            # connected but being moved, see HandleTool.on_button_press
            elif get_connection(h):
                r, g, b = 1, 0.6, 0
            elif h.movable:
                r, g, b = 0, 1, 0
            else:
                r, g, b = 0, 0, 1

            cairo.identity_matrix()
            cairo.set_antialias(ANTIALIAS_NONE)
            cairo.translate(*i2v.transform_point(*h.pos))
            cairo.rectangle(-4, -4, 8, 8)
            if inner:
                cairo.rectangle(-3, -3, 6, 6)
            cairo.set_source_rgba(r, g, b, opacity)
            cairo.fill_preserve()
            if h.connectable:
                cairo.move_to(-2, -2)
                cairo.line_to(2, 3)
                cairo.move_to(2, -2)
                cairo.line_to(-2, 3)
            cairo.set_source_rgba(r / 4.0, g / 4.0, b / 4.0, opacity * 1.3)
            cairo.stroke()
        cairo.restore()

    def paint(self, context):
        view = self.view
        canvas = view.canvas
        cairo = context.cairo
        selection = view.selection
        # Order matters here:
        for item in canvas.sort(selection.selected_items):
            self._draw_handles(item, cairo)
        # Draw nice opaque handles when hovering an item:
        item = selection.hovered_item
        if item and item not in selection.selected_items:
            self._draw_handles(item, cairo, opacity=0.25)
        item = selection.dropzone_item
        if item and item not in selection.selected_items:
            self._draw_handles(item, cairo, opacity=0.25, inner=True)
