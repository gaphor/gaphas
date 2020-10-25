"""The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes care of a layer in the canvas (such as grid, items
and handles).
"""

from typing import Sequence

from typing_extensions import Protocol

from gaphas.item import Item


class Painter(Protocol):
    """Painter interface."""

    def paint(self, items: Sequence[Item], cairo):
        """Do the paint action (called from the View)."""
        pass
