"""Tools are used to add interactive behavior to a View.
"""

import cairo
import gtk

DEBUG_TOOL = False


class Tool(object):

    def __init__(self):
        pass

    def on_button_press(self, view, event):
        """Mouse (pointer) button click. A button press is normally followed by
        a button release. Double and triple clicks should work together with
        the button methods.

        A single click is emited as:
                on_button_press
                on_button_release

        In case of a double click:
                single click +
                on_button_press
                on_double_click
                on_button_release

        In case of a tripple click:
                double click +
                on_button_press
                on_triple_click
                on_button_release
        """
        if DEBUG_TOOL: print 'on_button_press', view, event

    def on_button_release(self, view, event):
        """Button release event, that follows on a button press event.
        Not that double and tripple clicks'...
        """
        if DEBUG_TOOL: print 'on_button_release', view, event
        pass

    def on_double_click(self, view, event):
        """Event emited when the user does a double click (click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_double_click', view, event
        pass

    def on_triple_click(self, view, event):
        """Event emited when the user does a triple click (click-click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_triple_click', view, event
        pass

    def on_motion_notify(self, view, event):
        """Mouse (pointer) is moved.
        """
        if DEBUG_TOOL: print 'on_motion_notify', view, event
        pass

    def on_key_press(self, view, event):
        """Keyboard key is pressed.
        """
        if DEBUG_TOOL: print 'on_key_press', view, event
        pass

    def on_key_release(self, view, event):
        """Keyboard key is released again (follows a key press normally).
        """
        if DEBUG_TOOL: print 'on_key_release', view, event
        pass


class DefaultTool(Tool):

    def __init__(self):
        self.last_x = 0
        self.last_y = 0

    def on_button_press(self, view, event):
        self.last_x, self.last_y = event.x, event.y
        # Deselect all items unless CTRL or SHIFT is pressed
        # or the item is already selected.
        if not (event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
                or view.hovered_item in view.selected_items) :
            del view.selected_items
        if view.hovered_item:
            view.focused_item = view.hovered_item

    def on_motion_notify(self, view, event):
        """Normally, just check which item is under the mouse pointer
        and make it the view.hovered_item.
        
        """
        if event.state & gtk.gdk.BUTTON_PRESS_MASK:
            for i in view.selected_items:
                # Set a redraw request before the item is updated
                view.queue_draw_item(i, handles=True)

                # Calculate the distance the item has to be moved
                inverse = cairo.Matrix(*tuple(i._matrix_w2i))
                inverse.invert()
                dx, dy = event.x - self.last_x, event.y - self.last_y
                # Move the item and schedule it for an update
                i.matrix.translate(*inverse.transform_distance(dx, dy))
                i.request_update()
                i.canvas.update_matrices()
                b = i._view_bounds
                view.queue_draw_item(i, handles=True)
                view.queue_draw_area(b[0] + dx, b[1] + dy, b[2] - b[0], b[3] - b[1])
        else:
            old_hovered = view.hovered_item
            view.hovered_item = view.get_item_at_point(event.x, event.y)
        self.last_x, self.last_y = event.x, event.y
        return True

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
