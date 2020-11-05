from typing import Sequence

from gaphas.canvas import Context
from gaphas.item import Item


class ToolPainter:
    """ToolPainter allows the Tool defined on a view to do some special
    drawing."""

    def __init__(self, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            view: (bool): write your description
        """
        assert view
        self.view = view

    def paint(self, items: Sequence[Item], cairo):
        """
        Paint the given item.

        Args:
            self: (todo): write your description
            items: (todo): write your description
            cairo: (todo): write your description
        """
        view = self.view
        if view.tool:
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(Context(items=items, cairo=cairo))
            cairo.restore()
