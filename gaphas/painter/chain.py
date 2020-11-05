from __future__ import annotations

from typing import List, Sequence

from gaphas.item import Item
from gaphas.painter.painter import Painter


class PainterChain:
    """Chain up a set of painters.

    like ToolChain.
    """

    def __init__(self):
        """
        Initialize the list of modules.

        Args:
            self: (todo): write your description
        """
        self._painters: List[Painter] = []

    def append(self, painter: Painter) -> PainterChain:
        """Add a painter to the list of painters."""
        self._painters.append(painter)
        return self

    def prepend(self, painter: Painter) -> PainterChain:
        """Add a painter to the beginning of the list of painters."""
        self._painters.insert(0, painter)
        return self

    def paint(self, items: Sequence[Item], cairo):
        """See Painter.paint()."""
        for painter in self._painters:
            painter.paint(items, cairo)
