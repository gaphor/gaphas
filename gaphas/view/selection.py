from typing import Callable, Set


class Selection:
    def __init__(self):
        super().__init__()
        # Handling selections.
        self._selected_items = set()
        self._focused_item = None
        self._hovered_item = None
        self._dropzone_item = None
        self._handlers: Set[Callable[[], None]] = set()

    def add_handler(self, handler: Callable[[], None]) -> None:
        """Add a callback handler, triggered when a constraint is resolved."""
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[], None]) -> None:
        """Remove a previously assigned handler."""
        self._handlers.discard(handler)

    def notify(self) -> None:
        for handler in self._handlers:
            handler()

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
                self.notify()

    def unselect_item(self, item):
        if item is self._hovered_item:
            self.set_hovered_item(None)
        if item is self._dropzone_item:
            self.set_dropzone_item(None)
        if item is self._focused_item:
            self.set_focused_item(None)
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.notify()

    def set_focused_item(self, item):
        if item:
            self.select_items(item)

        if item is not self._focused_item:
            self._focused_item = item
            self.notify()

    def set_hovered_item(self, item):
        if item is not self._hovered_item:
            self._hovered_item = item
            self.notify()

    def set_dropzone_item(self, item):
        if item is not self._dropzone_item:
            self._dropzone_item = item
            self.notify()

    def unselect_all(self):
        """Clearing the selected_item also clears the focused_item."""
        for item in list(self._selected_items):
            self.unselect_item(item)
        self.set_focused_item(None)
