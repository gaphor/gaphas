from __future__ import annotations

from typing import TYPE_CHECKING, Collection

from gaphas.item import Item
from gaphas.types import CairoContext

if TYPE_CHECKING:
    from gaphas.view import GtkView


class RenderedItemPainter:
    def __init__(self, view: GtkView) -> None:
        assert view
        self.view = view

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        for item in items:
            surface = self.view.rendered_item(item)
            cairo.set_source_surface(surface)  # type: ignore[attr-defined]
            cairo.paint()
