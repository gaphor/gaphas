from gi.repository import Gdk

from gaphas.view import GtkView


class Tool:
    """Base class for a tool. This class A word on click events:

    Mouse (pointer) button click. A button press is normally followed
    by a button release. Double and triple clicks should work together
    with the button methods.

    A single click is emitted as:
            on_button_press
            on_button_release

    In case of a double click:
            on_button_press (x 2)
            on_double_click
            on_button_release

    In case of a triple click:
            on_button_press (x 3)
            on_triple_click
            on_button_release
    """

    # Custom events:
    GRAB = -100
    UNGRAB = -101

    # Map GDK events to tool methods
    EVENT_HANDLERS = {
        Gdk.EventType.BUTTON_PRESS: "on_button_press",
        Gdk.EventType.BUTTON_RELEASE: "on_button_release",
        Gdk.EventType._2BUTTON_PRESS: "on_double_click",
        Gdk.EventType._3BUTTON_PRESS: "on_triple_click",
        Gdk.EventType.MOTION_NOTIFY: "on_motion_notify",
        Gdk.EventType.KEY_PRESS: "on_key_press",
        Gdk.EventType.KEY_RELEASE: "on_key_release",
        Gdk.EventType.SCROLL: "on_scroll",
        # Custom events:
        GRAB: "on_grab",
        UNGRAB: "on_ungrab",
    }

    # Those events force the tool to release the grabbed tool.
    FORCE_UNGRAB_EVENTS = (Gdk.EventType._2BUTTON_PRESS, Gdk.EventType._3BUTTON_PRESS)

    def __init__(self, view: GtkView):
        self.view = view

    def _dispatch(self, event: Gdk.Event):
        """Deal with the event.

        The event is dispatched to a specific handler for the event
        type.
        """
        handler = self.EVENT_HANDLERS.get(event.type)
        if handler:
            try:
                h = getattr(self, handler)
            except AttributeError:
                pass  # No handler
            else:
                return bool(h(event))
        return False

    def handle(self, event: Gdk.Event):
        return self._dispatch(event)

    def draw(self, context):
        """Some tools (such as Rubberband selection) may need to draw something
        on the canvas. This can be done through the draw() method. This is
        called after all items are drawn. The context contains the following
        fields:

        - context: the render context (contains context.view and context.cairo)
        - cairo: the Cairo drawing context
        """
        pass
