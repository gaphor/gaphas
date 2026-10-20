from __future__ import annotations

import enum
from collections.abc import Callable, Collection

from gaphas.item import Item


class SelectionFlags(enum.Flag):
    SELECTED = enum.auto()
    FOCUSED = enum.auto()
    HOVERED = enum.auto()
    ALL = SELECTED | FOCUSED | HOVERED


class Selection:
    def __init__(self):
        super().__init__()
        self._selected_items: set[Item] = set()
        self._focused_item: Item | None = None
        self._hovered_item: Item | None = None
        self._handlers: set[tuple[SelectionFlags, Callable[[Item | None], None]]] = (
            set()
        )

    def add_handler(
        self,
        handler: Callable[[Item | None], None],
        flags: SelectionFlags = SelectionFlags.ALL,
    ) -> None:
        """Add a callback handler, triggered when a constraint is resolved."""
        self._handlers.add((flags, handler))

    def remove_handler(self, handler: Callable[[Item | None], None]) -> None:
        """Remove a previously assigned handler."""
        to_be_discarded = [e for e in self._handlers if e[1] == handler]
        for e in to_be_discarded:
            self._handlers.discard(e)

    def notify(
        self, item: Item | None, flags: SelectionFlags = SelectionFlags.ALL
    ) -> None:
        for flag, handler in self._handlers:
            if flags in flag:
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
