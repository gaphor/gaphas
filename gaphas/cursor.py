from __future__ import annotations

from functools import singledispatch
from typing import Union

from gaphas.connector import Handle
from gaphas.item import Element, Item, Line
from gaphas.types import Pos

DEFAULT_CURSOR = "default"


@singledispatch
def cursor(item: Union[Item, None], handle: Union[Handle, None], pos: Pos) -> str:
    return DEFAULT_CURSOR


ELEMENT_CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")


@cursor.register
def element_hover(item: Element, handle: Union[Handle, None], pos: Pos) -> str:
    if handle:
        index = item.handles().index(handle)
        return ELEMENT_CURSORS[index] if index < 4 else DEFAULT_CURSOR
    return DEFAULT_CURSOR


LINE_CURSOR = "move"


@cursor.register
def line_hover(item: Line, handle: Union[Handle, None], pos: Pos) -> str:
    return LINE_CURSOR if handle else DEFAULT_CURSOR
