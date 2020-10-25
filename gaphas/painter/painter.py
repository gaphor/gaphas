"""The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes care of a layer in the canvas (such as grid, items
and handles).
"""


class Painter:
    """Painter interface."""

    def __init__(self, view=None):
        self.view = view

    def set_view(self, view):
        self.view = view

    def paint(self, context):
        """Do the paint action (called from the View)."""
        pass
