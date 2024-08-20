from __future__ import annotations

from collections.abc import Callable, Collection

from gaphas.item import Item


class Selection:
    def __init__(self):
        super().__init__()
        self._selected_items: set[Item] = set()
        self._focused_item: Item | None = None
        self._hovered_item: Item | None = None
        self._handlers: set[Callable[[Item | None], None]] = set()

    def add_handler(self, handler: Callable[[Item | None], None]) -> None:
        """Add a callback handler, triggered when a constraint is resolved."""
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Item | None], None]) -> None:
        """Remove a previously assigned handler."""
        self._handlers.discard(handler)

    def notify(self, item: Item | None) -> None:
        for handler in self._handlers:
            handler(item)

    def clear(self):
        self._selected_items.clear()
        self._focused_item = None
        self._hovered_item = None
        self.notify(None)

    @property
    def selected_items(self) -> Collection[Item]:
        return self._selected_items

    def select_items(self, *items: Item) -> None:
        for item in items:
            if item not in self._selected_items:
                self._selected_items.add(item)
                self.notify(item)

    def unselect_item(self, item: Item) -> None:
        """Unselect an item.

        If it's focused, it will be unfocused as well.
        """
        if item is self._focused_item:
            self._focused_item = None
        if item in self._selected_items:
            self._selected_items.discard(item)
            self.notify(item)

    def unselect_all(self) -> None:
        """Clearing the selected_item also clears the focused_item."""
        for item in list(self._selected_items):
            self.unselect_item(item)
        self.focused_item = None

    @property
    def focused_item(self) -> Item | None:
        return self._focused_item

    @focused_item.setter
    def focused_item(self, item: Item | None) -> None:
        if item:
            self.select_items(item)

        if item is not self._focused_item:
            self._focused_item = item
            self.notify(item)

    @property
    def hovered_item(self) -> Item | None:
        return self._hovered_item

    @hovered_item.setter
    def hovered_item(self, item: Item | None) -> None:
        if item is not self._hovered_item:
            self._hovered_item = item
            self.notify(item)
