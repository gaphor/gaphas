from __future__ import annotations

from typing import TYPE_CHECKING, Collection

from cairo import ANTIALIAS_NONE

from gaphas.item import Item
from gaphas.types import CairoContext

if TYPE_CHECKING:
    from gaphas.view import GtkView


class HandlePainter:
    """Draw handles of items that are marked as selected in the view."""

    def __init__(self, view: GtkView) -> None:
        assert view
        self.view = view

    def _draw_handles(
        self,
        item: Item,
        cairo: CairoContext,
        opacity: float | None = None,
    ) -> None:
        """Draw handles for an item.

        The handles are drawn in non-antialiased mode for clarity.
        """
        view = self.view
        model = view.model
        assert model
        cairo.save()
        if not opacity:
            opacity = (item is view.selection.focused_item) and 0.7 or 0.4

        cairo.set_antialias(ANTIALIAS_NONE)
        cairo.set_line_width(1)

        get_connection = model.connections.get_connection
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

            vx, vy = cairo.user_to_device(*item.matrix_i2c.transform_point(*h.pos))

            cairo.save()
            cairo.identity_matrix()
            cairo.translate(vx, vy)
            cairo.rectangle(-4, -4, 8, 8)
            cairo.set_source_rgba(r, g, b, opacity)
            cairo.fill_preserve()
            cairo.set_source_rgba(r / 4.0, g / 4.0, b / 4.0, opacity * 1.3)
            cairo.stroke()
            if h.connectable:
                cairo.rectangle(-2, -2, 4, 4)
                cairo.fill()
            cairo.restore()
        cairo.restore()

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        view = self.view
        model = view.model
        assert model
        selection = view.selection
        # Order matters here:
        for item in model.sort(selection.selected_items):
            self._draw_handles(item, cairo)
        # Draw nice opaque handles when hovering an item:
        hovered = selection.hovered_item
        if hovered and hovered not in selection.selected_items:
            self._draw_handles(hovered, cairo, opacity=0.25)
