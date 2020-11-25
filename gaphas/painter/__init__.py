from gaphas.painter.boundingboxpainter import BoundingBoxPainter
from gaphas.painter.chain import PainterChain
from gaphas.painter.freehand import FreeHandPainter
from gaphas.painter.handlepainter import HandlePainter
from gaphas.painter.itempainter import ItemPainter
from gaphas.painter.painter import Painter


def DefaultPainter(view) -> Painter:
    """Default painter, containing item, handle and tool painters."""
    return (
        PainterChain().append(ItemPainter(view.selection)).append(HandlePainter(view))
    )
