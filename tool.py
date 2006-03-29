"""Tools are used to add interactive behavior to a View.
"""

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
        pass

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

