from __future__ import annotations

from typing import TYPE_CHECKING

from gaphas.painter.chain import PainterChain
from gaphas.painter.freehand import FreeHandPainter
from gaphas.painter.handlepainter import HandlePainter
from gaphas.painter.itempainter import ItemPainter
from gaphas.painter.painter import Painter

if TYPE_CHECKING:
    from gaphas.view import GtkView


def DefaultPainter(view: GtkView) -> Painter:
    """Default painter, containing item, handle and tool painters."""
    return (
        PainterChain().append(ItemPainter(view.selection)).append(HandlePainter(view))
    )
