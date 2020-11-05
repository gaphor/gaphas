from gi.repository import Gdk

from gaphas.aspect import InMotion, Selection
from gaphas.tool.tool import Tool


class ItemTool(Tool):
    """ItemTool does selection and dragging of items. On a button click, the
    currently "hovered item" is selected. If CTRL or SHIFT are pressed, already
    selected items remain selected. The last selected item gets the focus (e.g.
    receives key press events).

    The roles used are Selection (select, unselect) and InMotion (move).
    """

    def __init__(self, view=None, buttons=(1,)):
        """
        Initializes the view to the view.

        Args:
            self: (todo): write your description
            view: (bool): write your description
            buttons: (todo): write your description
        """
        super().__init__(view)
        self._buttons = buttons
        self._movable_items = set()

    def get_item(self):
        """
        Get the currently selected item

        Args:
            self: (todo): write your description
        """
        return self.view.selection.hovered_item

    def movable_items(self):
        """Filter the items that should eventually be moved.

        Returns InMotion aspects for the items.
        """
        view = self.view
        get_ancestors = view.canvas.get_ancestors
        selected_items = set(view.selection.selected_items)
        for item in selected_items:
            # Do not move subitems of selected items
            if not set(get_ancestors(item)).intersection(selected_items):
                yield InMotion(item, view)

    def on_button_press(self, event):
        """
        Called when the user press event.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        # TODO: make keys configurable
        view = self.view
        item = self.get_item()

        if event.get_button()[1] not in self._buttons:
            return False

        # Deselect all items unless CTRL or SHIFT is pressed
        # or the item is already selected.
        if not (
            event.get_state()[1]
            & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
            or item in view.selection.selected_items
        ):
            view.selection.unselect_all()

        if item:
            if (
                view.selection.hovered_item in view.selection.selected_items
                and event.get_state()[1] & Gdk.ModifierType.CONTROL_MASK
            ):
                selection = Selection(item, view)
                selection.unselect()
            else:
                selection = Selection(item, view)
                selection.select()
                self._movable_items.clear()
            return True

    def on_button_release(self, event):
        """
        Reimplement qt method.

        Args:
            self: (todo): write your description
            event: (todo): write your description
        """
        if event.get_button()[1] not in self._buttons:
            return False
        for inmotion in self._movable_items:
            inmotion.stop_move()
        self._movable_items.clear()
        return True

    def on_motion_notify(self, event):
        """Normally do nothing.

        If a button is pressed move the items around.
        """
        if event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK:

            if not self._movable_items:
                self._movable_items = set(self.movable_items())
                for inmotion in self._movable_items:
                    inmotion.start_move(event.get_coords()[1:])

            for inmotion in self._movable_items:
                inmotion.move(event.get_coords()[1:])

            return True
