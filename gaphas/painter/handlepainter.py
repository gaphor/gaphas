from __future__ import annotations

from typing import TYPE_CHECKING, Collection

from cairo import Context as CairoContext

from gaphas.item import Item

if TYPE_CHECKING:
    from gaphas.view import GtkView


# Colors from the GNOME Palette
RED_4 = (0.753, 0.110, 0.157)
ORANGE_4 = (0.902, 0.380, 0)
GREEN_4 = (0.180, 0.7608, 0.494)
BLUE_4 = (0.110, 0.443, 0.847)


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
            opacity = 0.9 if item is view.selection.focused_item else 0.6

        get_connection = model.connections.get_connection
        for h in item.handles():
            if not h.visible:
                continue
            # connected and not being moved, see HandleTool.on_button_press
            if get_connection(h):
                color = RED_4
            elif h.glued:
                color = ORANGE_4
            elif h.movable:
                color = GREEN_4
            else:
                color = BLUE_4

            vx, vy = cairo.user_to_device(*item.matrix_i2c.transform_point(*h.pos))
            cairo.set_source_rgba(*color, opacity)

            draw_handle(cairo, vx, vy)

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


def draw_handle(
    cairo: CairoContext, vx: float, vy: float, size: float = 12.0, corner: float = 2.0
) -> None:
    """Draw a handle with rounded corners."""
    radius = size / 2.0
    lower_right = size - corner

    pi_05 = 0.5 * 3.142
    pi = 3.142
    pi_15 = 1.5 * 3.142

    cairo.save()
    cairo.identity_matrix()
    cairo.translate(vx - radius, vy - radius)

    cairo.move_to(0.0, corner)
    cairo.arc(corner, corner, corner, pi, pi_15)
    cairo.line_to(lower_right, 0.0)
    cairo.arc(lower_right, corner, corner, pi_15, 0)
    cairo.line_to(size, lower_right)
    cairo.arc(lower_right, lower_right, corner, 0, pi_05)
    cairo.line_to(corner, size)
    cairo.arc(corner, lower_right, corner, pi_05, pi)
    cairo.close_path()
    cairo.fill()
    cairo.restore()
