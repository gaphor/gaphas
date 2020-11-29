from gi.repository import GObject


class Selection(GObject.Object):
    # Just defined a name to make GTK register this class.
    __gtype_name__ = "GaphasSelection"

    # Signals: emitted after the change takes effect.
    __gsignals__ = {
        "dropzone-changed": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,),
        ),
        "hover-changed": (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
        "focus-changed": (GObject.SignalFlags.RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
        "selection-changed": (
            GObject.SignalFlags.RUN_LAST,
            None,
            (GObject.TYPE_PYOBJECT,),
        ),
    }

    def __init__(self):
        super().__init__()
        # Handling selections.
        self._selected_items = set()
        self._focused_item = None
        self._hovered_item = None
        self._dropzone_item = None

    def clear(self):
        self._selected_items.clear()
        self._focused_item = None
        self._hovered_item = None
        self._dropzone_item = None

    @property
    def selected_items(self):
        return self._selected_items

    @property
    def focused_item(self):
        return self._focused_item

    @property
    def hovered_item(self):
        return self._hovered_item

    @property
    def dropzone_item(self):
        return self._dropzone_item

    def select_items(self, *items):
        for item in items:
            if item not in self._selected_items:
                self._selected_items.add(item)
                self.emit("selection-changed", self._selected_items)

    def unselect_item(self, item):
        if item is self._focused_item:
            self.set_focused_item(None)
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.emit("selection-changed", self._selected_items)

    def set_focused_item(self, item):
        if item:
            self.select_items(item)

        if item is not self._focused_item:
            self._focused_item = item
            self.emit("focus-changed", item)

    def set_hovered_item(self, item):
        if item is not self._hovered_item:
            self._hovered_item = item
            self.emit("hover-changed", item)

    def set_dropzone_item(self, item):
        if item is not self._dropzone_item:
            self._dropzone_item = item
            self.emit("dropzone-changed", item)

    def unselect_all(self):
        """Clearing the selected_item also clears the focused_item."""
        for item in list(self._selected_items):
            self.unselect_item(item)
        self.set_focused_item(None)
