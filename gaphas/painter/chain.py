class PainterChain:
    """Chain up a set of painters.

    like ToolChain.
    """

    def __init__(self):
        self._painters = []

    def append(self, painter):
        """Add a painter to the list of painters."""
        self._painters.append(painter)
        return self

    def prepend(self, painter):
        """Add a painter to the beginning of the list of painters."""
        self._painters.insert(0, painter)

    def paint(self, context):
        """See Painter.paint()."""
        for painter in self._painters:
            painter.paint(context)
