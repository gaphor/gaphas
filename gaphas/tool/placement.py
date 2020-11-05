from gaphas.tool.tool import Tool


class PlacementTool(Tool):
    def __init__(self, view, factory, handle_tool, handle_index):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            view: (bool): write your description
            factory: (float): write your description
            handle_tool: (todo): write your description
            handle_index: (int): write your description
        """
        super().__init__(view)
        self._factory = factory
        self.handle_tool = handle_tool
        handle_tool.set_view(view)
        self._handle_index = handle_index
        self._new_item = None
        self.grabbed_handle = None

    # handle_tool = property(lambda s: s._handle_tool, doc="Handle tool")
    handle_index = property(
        lambda s: s._handle_index, doc="Index of handle to be used by handle_tool"
    )
    new_item = property(lambda s: s._new_item, doc="The newly created item")

    def on_button_press(self, event):
        """
        Handle the mouse press press press.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
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
        """
        Create a new item

        Args:
            self: (todo): write your description
            pos: (int): write your description
            kw: (dict): write your description
        """
        view = self.view
        item = self._factory(**kw)
        x, y = view.get_matrix_v2i(item).transform_point(*pos)
        item.matrix.translate(x, y)
        return item

    def on_button_release(self, event):
        """
        Reimplemented release events.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if self.grabbed_handle:
            self.handle_tool.on_button_release(event)
            self.grabbed_handle = None
        self._new_item = None
        return True

    def on_motion_notify(self, event):
        """
        Called when a motion event.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if self.grabbed_handle:
            return self.handle_tool.on_motion_notify(event)
        else:
            # act as if the event is handled if we have a new item
            return bool(self._new_item)
