from gaphas.aspect import PaintFocused


class FocusedItemPainter:
    """This painter allows for drawing on top of all the other layers for the
    focused item."""

    def __init__(self, view):
        assert view
        self.view = view

    def paint(self, context):
        view = self.view
        item = view.selection.hovered_item
        if item and item is view.selection.focused_item:
            PaintFocused(item, view).paint(context)
