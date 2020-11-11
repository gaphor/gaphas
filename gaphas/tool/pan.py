from gi.repository import Gdk

from gaphas.tool.tool import Tool

PAN_MASK = (
    Gdk.ModifierType.SHIFT_MASK
    | Gdk.ModifierType.MOD1_MASK
    | Gdk.ModifierType.CONTROL_MASK
)
PAN_VALUE = 0


class PanTool(Tool):
    """Captures drag events with the middle mouse button and uses them to
    translate the canvas within the view.

    Trumps the ZoomTool, so should be placed later in the ToolChain.
    """

    def __init__(self, view):
        super().__init__(view)
        self.x0, self.y0 = 0, 0
        self.speed = 10

    def on_button_press(self, event):
        if event.get_state()[1] & PAN_MASK != PAN_VALUE:
            return False
        if event.get_button()[1] == 2:
            self.x0, self.y0 = event.get_coords()[1:]
            return True

    def on_button_release(self, event):
        self.x0, self.y0 = event.get_coords()[1:]
        return True

    def on_motion_notify(self, event):
        if event.get_state()[1] & Gdk.ModifierType.BUTTON2_MASK:
            view = self.view
            self.x1, self.y1 = event.get_coords()[1:]
            dx = self.x1 - self.x0
            dy = self.y1 - self.y0
            view._matrix.translate(dx / view._matrix[0], dy / view._matrix[3])
            # Make sure everything's updated
            view.request_update((), view.canvas.get_all_items())
            self.x0 = self.x1
            self.y0 = self.y1
            return True

    def on_scroll(self, event):
        # Ensure no modifiers
        if event.get_state()[1] & PAN_MASK != PAN_VALUE:
            return False
        view = self.view
        direction = event.get_scroll_direction()[1]
        if direction == Gdk.ScrollDirection.LEFT:
            view._matrix.translate(self.speed / view._matrix[0], 0)
        elif direction == Gdk.ScrollDirection.RIGHT:
            view._matrix.translate(-self.speed / view._matrix[0], 0)
        elif direction == Gdk.ScrollDirection.UP:
            view._matrix.translate(0, self.speed / view._matrix[3])
        elif direction == Gdk.ScrollDirection.DOWN:
            view._matrix.translate(0, -self.speed / view._matrix[3])
        view.request_update((), view.canvas.get_all_items())
        return True
