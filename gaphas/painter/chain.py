from gaphas.painter.painter import Painter


class PainterChain(Painter):
    """Chain up a set of painters.

    like ToolChain.
    """

    def __init__(self, view=None):
        super().__init__(view)
        self._painters = []

    def set_view(self, view):
        self.view = view
        for painter in self._painters:
            painter.set_view(self.view)

    def append(self, painter):
        """Add a painter to the list of painters."""
        self._painters.append(painter)
        painter.set_view(self.view)
        return self

    def prepend(self, painter):
        """Add a painter to the beginning of the list of painters."""
        self._painters.insert(0, painter)

    def paint(self, context):
        """See Painter.paint()."""
        for painter in self._painters:
            painter.paint(context)
