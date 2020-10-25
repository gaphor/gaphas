from gaphas.painter.painter import Painter


class ToolPainter(Painter):
    """ToolPainter allows the Tool defined on a view to do some special
    drawing."""

    def paint(self, context):
        view = self.view
        if view.tool:
            cairo = context.cairo
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(context)
            cairo.restore()
