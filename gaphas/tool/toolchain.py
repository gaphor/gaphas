from gi.repository import Gdk

from gaphas.canvas import Context
from gaphas.tool.tool import Tool

DEBUG_TOOL_CHAIN = False

Event = Context


class ToolChain(Tool):
    """A ToolChain can be used to chain tools together, for example HoverTool,
    HandleTool, SelectionTool.

    The grabbed item is bypassed in case a double or triple click event
    is received. Should make sure this doesn't end up in dangling
    states.
    """

    def __init__(self, view=None):
        super().__init__(view)
        self._tools = []
        self._grabbed_tool = None

    def set_view(self, view):
        self.view = view
        for tool in self._tools:
            tool.set_view(self.view)

    def append(self, tool):
        """Append a tool to the chain.

        Self is returned.
        """
        self._tools.append(tool)
        tool.view = self.view
        return self

    def grab(self, tool):
        if not self._grabbed_tool:
            if DEBUG_TOOL_CHAIN:
                print("Grab tool", tool)
            # Send grab event
            event = Event(type=Tool.GRAB)
            tool.handle(event)
            self._grabbed_tool = tool

    def ungrab(self, tool):
        if self._grabbed_tool is tool:
            if DEBUG_TOOL_CHAIN:
                print("UNgrab tool", self._grabbed_tool)
            # Send ungrab event
            event = Event(type=Tool.UNGRAB)
            tool.handle(event)
            self._grabbed_tool = None

    def validate_grabbed_tool(self, event):
        """Check if it's valid to have a grabbed tool on an event.

        If not the grabbed tool will be released.
        """
        if event.type in self.FORCE_UNGRAB_EVENTS:
            self.ungrab(self._grabbed_tool)

    def handle(self, event):
        """Handle the event by calling each tool until the event is handled or
        grabbed.

        If a tool is returning True on a button press event, the motion
        and button release events are also passed to this
        """
        handler = self.EVENT_HANDLERS.get(event.type)

        self.validate_grabbed_tool(event)

        if self._grabbed_tool and handler:
            try:
                return self._grabbed_tool.handle(event)
            finally:
                if event.type == Gdk.EventType.BUTTON_RELEASE:
                    self.ungrab(self._grabbed_tool)
        else:
            for tool in self._tools:
                if DEBUG_TOOL_CHAIN:
                    print("tool", tool)
                rt = tool.handle(event)
                if rt:
                    if event.type == Gdk.EventType.BUTTON_PRESS:
                        self.view.grab_focus()
                        self.grab(tool)
                    return rt

    def draw(self, context):
        if self._grabbed_tool:
            self._grabbed_tool.draw(context)
