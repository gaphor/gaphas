"""
Defines roles for Items. Roles are a means to add behaviour to an item.
"""

from roles import RoleType

class Selection(object):
    """
    A role for items. When dealing with selection.
    """
    __metaclass__ = RoleType

    def focus(self, view):
        view.focused_item = self

    def select(self, view, unselect=False):
        view.focused_item = this
        # Filter the items that should eventually be moved
        get_ancestors = view.canvas.get_ancestors
        selected_items = set(view.selected_items)
        for i in selected_items:
            # Do not move subitems of selected items
            if not set(get_ancestors(i)).intersection(selected_items):
                self._movable_items.add(i)

    def unselect(self, view):
        view.focused_item = None
        view.unselect_item(self)

    def move(self, event):
        # TODO: don't want events here
        pass


def Connecter(object):
    __metaclass__ = RoleType

    def connect_to(self, sink):
        pass

def Sink(object):
    __metaclass__ = RoleType


# vim:sw=4:et:ai
