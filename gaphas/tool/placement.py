from typing import Callable

from typing_extensions import Protocol

from gaphas.connector import Handle
from gaphas.item import Item
from gaphas.tool.tool import Tool
from gaphas.view import GtkView

FactoryType = Callable[..., Item]  # type: ignore[misc]


class HandleToolType(Protocol):
    def grab_handle(self, new_item: Item, handle: Handle):
        ...


class PlacementTool(Tool):
    def __init__(
        self,
        view: GtkView,
        factory: FactoryType,
        handle_tool: HandleToolType,
        handle_index: int,
    ):
        super().__init__(view)
        self._factory = factory
        self.handle_tool = handle_tool
        self._handle_index = handle_index
        self._new_item = None
        self.grabbed_handle = None

    handle_index = property(
        lambda s: s._handle_index, doc="Index of handle to be used by handle_tool"
    )
    new_item = property(lambda s: s._new_item, doc="The newly created item")

    def on_button_press(self, event):
        view = self.view
        pos = event.get_coords()[1:]
        new_item = self._create_item(pos)

        self._new_item = new_item
        view.selection.set_focused_item(new_item)

        h = new_item.handles()[self._handle_index]
        if h.movable:
            self.handle_tool.grab_handle(new_item, h)
            self.grabbed_handle = h
        return True

    def _create_item(self, pos, **kw):
        view = self.view
        item = self._factory(**kw)
        x, y = view.get_matrix_v2i(item).transform_point(*pos)
        item.matrix.translate(x, y)
        return item

    def on_button_release(self, event):
        if self.grabbed_handle:
            self.handle_tool.on_button_release(event)
            self.grabbed_handle = None
        self._new_item = None
        return True

    def on_motion_notify(self, event):
        if self.grabbed_handle:
            return self.handle_tool.on_motion_notify(event)
        else:
            # act as if the event is handled if we have a new item
            return bool(self._new_item)
