from typing import Optional

from gi.repository import Gtk

from gaphas.item import Item
from gaphas.tool.itemtool import handle_at_point, item_at_point
from gaphas.types import Pos
from gaphas.view import GtkView


def hover_tool(view: GtkView) -> Gtk.EventController:
    """Highlight the currenly hovered item."""
    ctrl = (
        Gtk.EventControllerMotion.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerMotion.new()
    )
    ctrl.connect("motion", on_motion)
    return ctrl


def on_motion(ctrl, x, y):
    view = ctrl.get_widget()
    view.selection.hovered_item = find_item_at_point(view, (x, y))


def find_item_at_point(view: GtkView, pos: Pos) -> Optional[Item]:
    item, handle = handle_at_point(view, pos)
    return item or item_at_point(view, pos)
