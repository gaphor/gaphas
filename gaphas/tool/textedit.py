from gi.repository import Gdk, Gtk

from gaphas.tool.tool import Tool


class TextEditTool(Tool):
    """Demo of a text edit tool (just displays a text edit box at the cursor
    position."""

    def __init__(self, view=None):
        super().__init__(view)

    def on_double_click(self, event):
        """Create a popup window with some editable text."""
        window = Gtk.Window()
        window.set_property("decorated", False)
        window.set_resize_mode(Gtk.ResizeMode.IMMEDIATE)
        # window.set_modal(True)
        window.set_parent_window(self.view.get_window())
        buffer = Gtk.TextBuffer()
        text_view = Gtk.TextView()
        text_view.set_buffer(buffer)
        text_view.show()
        window.add(text_view)
        rect = Gdk.Rectangle()
        pos = event.get_coords()[1:]
        rect.x, rect.y, rect.width, rect.height = int(pos[0]), int(pos[1]), 50, 50
        window.size_allocate(rect)
        # window.move(int(event.x), int(event.y))
        cursor_pos = self.view.get_toplevel().get_screen().get_display().get_pointer()
        window.move(cursor_pos[1], cursor_pos[2])
        window.connect("focus-out-event", self._on_focus_out_event, buffer)
        text_view.connect("key-press-event", self._on_key_press_event, buffer)
        # text_view.set_size_request(50, 50)
        window.show()
        # text_view.grab_focus()
        # window.set_uposition(event.x, event.y)
        # window.focus
        return True

    def _on_key_press_event(self, widget, event, buffer):
        # if event.keyval == Gdk.KEY_Return:
        #     widget.get_toplevel().destroy()
        if event.get_keyval()[1] == Gdk.KEY_Escape:
            widget.get_toplevel().destroy()

    def _on_focus_out_event(self, widget, event, buffer):
        widget.destroy()
