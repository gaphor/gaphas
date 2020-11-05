from gi.repository import Gdk

from gaphas.tool.tool import Tool

ZOOM_MASK = (
    Gdk.ModifierType.CONTROL_MASK
    | Gdk.ModifierType.SHIFT_MASK
    | Gdk.ModifierType.MOD1_MASK
)
ZOOM_VALUE = Gdk.ModifierType.CONTROL_MASK


class ZoomTool(Tool):
    """Tool for zooming.

    Uses two different user inputs to zoom:
    - Ctrl + middle-mouse dragging in the up-down direction.
    - Ctrl + mouse-wheel
    """

    def __init__(self, view=None):
        """
        Initialize the underlying view.

        Args:
            self: (todo): write your description
            view: (bool): write your description
        """
        super().__init__(view)
        self.x0, self.y0 = 0, 0
        self.lastdiff = 0

    def on_button_press(self, event):
        """
        Handle keyboard press press events.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if (
            event.get_button()[1] == 2
            and event.get_state()[1] & ZOOM_MASK == ZOOM_VALUE
        ):
            pos = event.get_coords()[1:]
            self.x0 = pos[0]
            self.y0 = pos[1]
            self.lastdiff = 0
            return True

    def on_button_release(self, event):
        """
        Return true if the keyboard button.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        self.lastdiff = 0
        return True

    def on_motion_notify(self, event):
        """
        Notify motion event handler

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if (
            event.get_state()[1] & ZOOM_MASK != ZOOM_VALUE
            or not event.get_state()[1] & Gdk.ModifierType.BUTTON2_MASK
        ):
            return

        view = self.view
        pos = event.get_coords()[1:]
        dy = pos[1] - self.y0

        sx = view._matrix[0]
        sy = view._matrix[3]
        ox = (view._matrix[4] - self.x0) / sx
        oy = (view._matrix[5] - self.y0) / sy

        if abs(dy - self.lastdiff) > 20:
            factor = 1.0 / 0.9 if dy - self.lastdiff < 0 else 0.9
            m = view.matrix
            m.translate(-ox, -oy)
            m.scale(factor, factor)
            m.translate(+ox, +oy)

            # Make sure everything's updated
            view.request_update((), view.canvas.get_all_items())

            self.lastdiff = dy
        return True

    def on_scroll(self, event):
        """
        Callback for scroll event.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if event.get_state()[1] & Gdk.ModifierType.CONTROL_MASK:
            view = self.view
            sx = view._matrix[0]
            sy = view._matrix[3]
            pos = event.get_coords()[1:]
            ox = (view._matrix[4] - pos[0]) / sx
            oy = (view._matrix[5] - pos[1]) / sy
            factor = 0.9
            if event.get_scroll_direction()[1] == Gdk.ScrollDirection.UP:
                factor = 1.0 / factor
            view._matrix.translate(-ox, -oy)
            view._matrix.scale(factor, factor)
            view._matrix.translate(+ox, +oy)
            # Make sure everything's updated
            view.request_update((), view.canvas.get_all_items())
            return True
