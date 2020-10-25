from gaphas.painter.boundingboxpainter import BoundingBoxPainter
from gaphas.painter.chain import PainterChain
from gaphas.painter.focuseditempainter import FocusedItemPainter
from gaphas.painter.handlepainter import HandlePainter
from gaphas.painter.itempainter import ItemPainter
from gaphas.painter.painter import Painter
from gaphas.painter.toolpainter import ToolPainter


def DefaultPainter(view) -> Painter:
    """Default painter, containing item, handle and tool painters."""
    return (
        PainterChain()
        .append(ItemPainter(view))
        .append(HandlePainter(view))
        .append(FocusedItemPainter(view))
        .append(ToolPainter(view))
    )
