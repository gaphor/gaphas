from typing import Sequence

from gaphas.canvas import Context
from gaphas.item import Item


class ToolPainter:
    """ToolPainter allows the Tool defined on a view to do some special
    drawing."""

    def __init__(self, view):
        assert view
        self.view = view

    def paint(self, items: Sequence[Item], cairo):
        view = self.view
        if view.tool:
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(Context(items=items, cairo=cairo))
            cairo.restore()
