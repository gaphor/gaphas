from gaphas.painter.boundingboxpainter import BoundingBoxPainter
from gaphas.painter.chain import PainterChain
from gaphas.painter.focuseditempainter import FocusedItemPainter
from gaphas.painter.handlepainter import HandlePainter
from gaphas.painter.itempainter import ItemPainter
from gaphas.painter.painter import Painter
from gaphas.painter.toolpainter import ToolPainter


def DefaultPainter(view=None):
    """Default painter, containing item, handle and tool painters."""
    return (
        PainterChain(view)
        .append(ItemPainter())
        .append(HandlePainter())
        .append(FocusedItemPainter())
        .append(ToolPainter())
    )
