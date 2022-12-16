from __future__ import annotations

from functools import singledispatch

from gi.repository import Gtk

from gaphas.connector import Handle
from gaphas.item import Element, Item, Line

DEFAULT_CURSOR = "left_ptr" if Gtk.get_major_version() == 3 else "default"


@singledispatch
def cursor(item: Item | None, handle: Handle | None) -> str:
    return DEFAULT_CURSOR


ELEMENT_CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")


@cursor.register
def element_hover(item: Element, handle: Handle | None) -> str:
    index = item.handles().index(handle)
    return ELEMENT_CURSORS[index] if index < 4 else DEFAULT_CURSOR


LINE_CURSOR = "fleur" if Gtk.get_major_version() == 3 else "move"


@cursor.register
def line_hover(item: Line, handle: Handle | None) -> str:
    return LINE_CURSOR if handle else DEFAULT_CURSOR
