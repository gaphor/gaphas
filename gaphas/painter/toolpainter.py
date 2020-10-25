class ToolPainter:
    """ToolPainter allows the Tool defined on a view to do some special
    drawing."""

    def __init__(self, view):
        assert view
        self.view = view

    def paint(self, context):
        view = self.view
        if view.tool:
            cairo = context.cairo
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(context)
            cairo.restore()
