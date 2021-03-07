from functools import singledispatch

from gaphas.item import Item
from gaphas.types import Pos
from gaphas.view import GtkView


class ItemMove:
    """Aspect for dealing with motion on an item.

    In this case the item is moved.
    """

    last_x: float
    last_y: float

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def start_move(self, pos: Pos) -> None:
        self.last_x, self.last_y = pos

    def move(self, pos: Pos) -> None:
        """Move the item.

        x and y are in view coordinates.
        """
        item = self.item
        view = self.view
        assert view.model

        v2i = view.get_matrix_v2i(item)
        x, y = pos
        dx, dy = x - self.last_x, y - self.last_y
        dx, dy = v2i.transform_distance(dx, dy)
        self.last_x, self.last_y = x, y

        item.matrix.translate(dx, dy)
        view.request_update([item])

    def stop_move(self, pos: Pos) -> None:
        pass


Move = singledispatch(ItemMove)
