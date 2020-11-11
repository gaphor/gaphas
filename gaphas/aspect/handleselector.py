from functools import singledispatch

from gi.repository import Gdk

from gaphas.connector import Handle
from gaphas.item import Element, Item
from gaphas.view import DEFAULT_CURSOR, GtkView


class ItemHandleSelection:
    """Deal with selection of the handle."""

    def __init__(self, item: Item, handle: Handle, view: GtkView):
        self.item = item
        self.handle = handle
        self.view = view

    def select(self):
        pass

    def unselect(self):
        pass


HandleSelection = singledispatch(ItemHandleSelection)


@HandleSelection.register(Element)
class ElementHandleSelection(ItemHandleSelection):
    CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")

    def select(self):
        index = self.item.handles().index(self.handle)
        if index < 4:
            display = self.view.get_display()
            cursor = Gdk.Cursor.new_from_name(display, self.CURSORS[index])
            self.view.get_window().set_cursor(cursor)

    def unselect(self):
        cursor = Gdk.Cursor(DEFAULT_CURSOR)
        self.view.get_window().set_cursor(cursor)
