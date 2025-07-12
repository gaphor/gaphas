from gi.repository import Gdk, Gtk

from typing import Callable, Union

from gaphas.cursor import cursor
from gaphas.tool.itemtool import default_find_item_and_handle_at_point
from gaphas.connector import Handle
from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView


def hover_tool(
    find_item_and_handle_at_point: Callable[
        [GtkView, Pos], Union[tuple[Item, Union[Handle, None]], tuple[None, None]]
    ] = default_find_item_and_handle_at_point,
) -> Gtk.EventController:
    """Highlight the currently hovered item."""
    ctrl = Gtk.EventControllerMotion.new()
    ctrl.connect("motion", on_motion, find_item_and_handle_at_point)
    ctrl.cursor_name = ""
    return ctrl


def on_motion(ctrl, x, y, find_item_and_handle_at_point):
    view = ctrl.get_widget()
    pos = (x, y)
    item, handle = find_item_and_handle_at_point(view, pos)
    view.selection.hovered_item = item

    if item:
        v2i = view.get_matrix_v2i(item)
        pos = v2i.transform_point(x, y)

    cursor_name = cursor(item, handle, pos)
    if cursor_name != ctrl.cursor_name:
        set_cursor(view, cursor_name)
        ctrl.cursor_name = cursor_name


def set_cursor(view, cursor_name):
    cursor = Gdk.Cursor.new_from_name(cursor_name)
    view.set_cursor(cursor)
