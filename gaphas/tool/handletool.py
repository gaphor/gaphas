from typing import Optional, Tuple

from gi.repository import Gdk
from typing_extensions import Protocol

from gaphas.aspect import Connector, HandleFinder, HandleInMotion, HandleSelection
from gaphas.connector import Handle
from gaphas.item import Item
from gaphas.tool.tool import Tool
from gaphas.view import GtkView

Pos = Tuple[float, float]


class HandleInMotionType(Protocol):
    def __init__(self, item: Item, handle: Handle, view: GtkView):
        ...

    def start_move(self, pos: Pos):
        ...

    def move(self, pos: Pos):
        ...

    def stop_move(self):
        ...

    def glue(self, pos: Pos, distance: float = 0):
        ...


class HandleTool(Tool):
    """Tool for moving handles around.

    By default this tool does not provide connecting handles to another
    item (see `ConnectHandleTool`).
    """

    def __init__(self, view):
        super().__init__(view)
        self.grabbed_handle: Optional[Handle] = None
        self.grabbed_item: Optional[Item] = None
        self.motion_handle: Optional[HandleInMotionType] = None

    def grab_handle(self, item: Item, handle: Handle):
        """Grab a specific handle.

        This can be used from the PlacementTool to set the state of the
        handle tool.
        """
        assert item is None and handle is None or handle in item.handles()
        self.grabbed_item = item
        self.grabbed_handle = handle

        selection = HandleSelection(item, handle, self.view)
        selection.select()

    def ungrab_handle(self):
        """Reset grabbed_handle and grabbed_item."""
        item = self.grabbed_item
        handle = self.grabbed_handle
        self.grabbed_handle = None
        self.grabbed_item = None
        if handle:
            selection = HandleSelection(item, handle, self.view)
            selection.unselect()

    def on_button_press(self, event):
        """Handle button press events.

        If the (mouse) button is pressed on top of a Handle
        (item.Handle), that handle is grabbed and can be dragged around.
        """
        view = self.view
        selection = view.selection

        item, handle = HandleFinder(selection.hovered_item, view).get_handle_at_point(
            event.get_coords()[1:]
        )

        if handle:
            # Deselect all items unless CTRL or SHIFT is pressed
            # or the item is already selected.
            # TODO: duplicate from ItemTool
            if not (
                event.get_state()[1]
                & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
                or selection.hovered_item in selection.selected_items
            ):
                selection.unselect_all()
            selection.set_hovered_item(item)
            selection.set_focused_item(item)

            self.motion_handle = None

            self.grab_handle(item, handle)

            return True

    def on_button_release(self, event):
        """Release a grabbed handle."""
        # queue extra redraw to make sure the item is drawn properly
        grabbed_handle, grabbed_item = self.grabbed_handle, self.grabbed_item

        if self.motion_handle:
            self.motion_handle.stop_move()
            self.motion_handle = None

        self.ungrab_handle()

        if grabbed_handle and grabbed_item:
            self.view.canvas.request_update(grabbed_item)
        return True

    def on_motion_notify(self, event):
        """Handle motion events.

        If a handle is grabbed: drag it around, else, if the pointer is
        over a handle, make the owning item the hovered-item.
        """
        if (
            self.grabbed_handle
            and event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK
        ):
            item = self.grabbed_item
            handle = self.grabbed_handle
            pos = event.get_coords()[1:]

            if self.motion_handle:
                self.motion_handle.move(pos)
            else:
                self.motion_handle = HandleInMotion(item, handle, self.view)
                assert self.motion_handle
                self.motion_handle.start_move(pos)

            return True


class ConnectHandleTool(HandleTool):
    """Tool for connecting two items.

    There are two items involved. Handle of connecting item (usually a
    line) is being dragged by an user towards another item (item in
    short). Port of an item is found by the tool and connection is
    established by creating a constraint between line's handle and
    item's port.
    """

    def glue(self, item: Item, handle: Handle, vpos: Pos):
        """Perform a small glue action to ensure the handle is at a proper
        location for connecting."""
        if self.motion_handle:
            return self.motion_handle.glue(vpos)
        else:
            return HandleInMotion(item, handle, self.view).glue(vpos)

    def connect(self, item: Item, handle: Handle, vpos: Pos):
        """Connect a handle of a item to connectable item.

        Connectable item is found by `ConnectHandleTool.glue` method.

        :Parameters:
         item
            Connecting item.
         handle
            Handle of connecting item.
         vpos
            Position to connect to (or near at least)
        """
        connections = self.view.canvas.connections
        connector = Connector(item, handle, connections)

        # find connectable item and its port
        sink = self.glue(item, handle, vpos)

        # no new connectable item, then diconnect and exit
        if sink:
            connector.connect(sink)
        else:
            cinfo = connections.get_connection(handle)
            if cinfo:
                connector.disconnect()

    def on_button_release(self, event):
        item = self.grabbed_item
        handle = self.grabbed_handle
        try:
            if item and handle and handle.connectable:
                pos = event.get_coords()[1:]
                self.connect(item, handle, pos)
        finally:
            return super().on_button_release(event)
