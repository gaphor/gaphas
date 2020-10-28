from gaphas.aspect import Finder
from gaphas.tool.tool import Tool


class HoverTool(Tool):
    """Make the item under the mouse cursor the "hovered item"."""

    def on_motion_notify(self, event):
        view = self.view
        pos = event.get_coords()[1:]
        view.selection.set_hovered_item(Finder(view).get_item_at_point(pos))
