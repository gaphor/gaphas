from gi.repository import Gdk

from gaphas.tool.tool import Tool


class RubberbandTool(Tool):
    def __init__(self, view=None):
        super().__init__(view)
        self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

    def on_button_press(self, event):
        self.x0, self.y0 = event.get_coords()[1:]
        self.x1, self.y1 = event.get_coords()[1:]
        return True

    def on_button_release(self, event):
        self.queue_draw(self.view)
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        items = self.view.get_items_in_rectangle(
            (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        )
        self.view.selection.select_items(*items)
        return True

    def on_motion_notify(self, event):
        if event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK:
            view = self.view
            self.queue_draw(view)
            self.x1, self.y1 = event.get_coords()[1:]
            self.queue_draw(view)
            return True

    def queue_draw(self, view):
        view.queue_redraw()

    def draw(self, context):
        cr = context.cairo
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        cr.set_source_rgba(0.9, 0.9, 0.9, 0.3)
        cr.fill_preserve()
        cr.set_line_width(2.0)
        cr.set_dash((7.0, 5.0), 0)
        cr.set_source_rgba(0.5, 0.5, 0.7, 0.7)
        cr.stroke()
