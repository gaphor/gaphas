from __future__ import annotations

from collections.abc import Collection

from cairo import Context as CairoContext

from gaphas.item import Item
from gaphas.painter.painter import Painter


class PainterChain:
    """Chain up a set of painters."""

    def __init__(self) -> None:
        self._painters: list[Painter] = []

    def append(self, painter: Painter) -> PainterChain:
        """Add a painter to the list of painters."""
        self._painters.append(painter)
        return self

    def prepend(self, painter: Painter) -> PainterChain:
        """Add a painter to the beginning of the list of painters."""
        self._painters.insert(0, painter)
        return self

    def paint(self, items: Collection[Item], cairo: CairoContext) -> None:
        """See Painter.paint()."""
        for painter in self._painters:
            painter.paint(items, cairo)
