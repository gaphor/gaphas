from __future__ import annotations

import logging
from functools import singledispatch
from operator import itemgetter
from typing import TYPE_CHECKING, Iterable, Sequence, Iterator

from gaphas.connector import ConnectionSink, ConnectionSinkType, Connector
from gaphas.handle import Handle
from gaphas.item import Item
from gaphas.types import Pos

if TYPE_CHECKING:
    from gaphas.view import GtkView

log = logging.getLogger(__name__)


class ItemHandleMove:
    """Move a handle (role is applied to the handle)"""

    GLUE_DISTANCE = 10

    last_x: float
    last_y: float

    def __init__(self, item: Item, handle: Handle, view: GtkView):
        self.item = item
        self.handle = handle
        self.view = view

    def start_move(self, pos: Pos) -> None:
        self.last_x, self.last_y = pos
        model = self.view.model
        assert model
        if cinfo := model.connections.get_connection(self.handle):
            self.handle.glued = True
            model.connections.solver.remove_constraint(cinfo.constraint)

    def move(self, pos: Pos) -> None:
        item = self.item
        view = self.view
        assert view.model

        v2i = view.get_matrix_v2i(item)

        x, y = v2i.transform_point(*pos)

        self.handle.pos = (x, y)

        self.handle.glued = bool(self.glue(pos))

        # do not request matrix update as matrix recalculation will be
        # performed due to item normalization if required
        view.model.request_update(item)

    def stop_move(self, pos: Pos) -> None:
        self.handle.glued = False
        self.connect(pos)

    def glue(
        self, pos: Pos, distance: int = GLUE_DISTANCE
    ) -> ConnectionSinkType | None:
        """Glue to an item near a specific point.

        Returns a ConnectionSink or None.
        """
        item = self.item
        handle = self.handle
        view = self.view
        model = view.model
        assert model
        connections = model.connections

        if not handle.connectable:
            return None

        for connectable in item_at_point(view, pos, distance=distance, exclude=(item,)):
            connector = Connector(self.item, self.handle, connections)
            sink = ConnectionSink(connectable)

            if connector.glue(sink):
                return sink

        return None

    def connect(self, pos: Pos) -> None:
        """Connect a handle of a item to connectable item.

        Connectable item is found by `ConnectHandleTool.glue` method.

        :Parameters:
         item
            Connecting item.
         handle
            Handle of connecting item.
         pos
            Position to connect to (or near at least)
        """
        handle = self.handle
        model = self.view.model
        assert model
        connections = model.connections
        connector = Connector(self.item, handle, connections)

        if sink := self.glue(pos):
            connector.connect(sink)
        elif connections.get_connection(handle):
            connector.disconnect()

        model.request_update(self.item)


HandleMove = singledispatch(ItemHandleMove)


def item_distance(
    view: GtkView,
    pos: Pos,
    distance: float = 0.5,
    exclude: Sequence[Item] = (),
) -> Iterable[tuple[float, Item]]:
    """Return the topmost item located at ``pos`` (x, y).

    Parameters:
        - view: a view
        - pos: Position, a tuple ``(x, y)`` in view coordinates
        - selected: if False returns first non-selected item
    """
    item: Item
    vx, vy = pos
    rect = (vx - distance, vy - distance, distance * 2, distance * 2)
    for item in reversed(list(view.get_items_in_rectangle(rect))):
        if item in exclude:
            continue

        v2i = view.get_matrix_v2i(item)
        ix, iy = v2i.transform_point(vx, vy)
        d = item.point(ix, iy)
        if d is None:
            log.warning("Item distance is None for %s", item)
            continue
        if d < distance:
            yield d, item


def order_items(distance_items, key=itemgetter(0)):
    inside = []
    outside = []
    for e in distance_items:
        if key(e) > 0:
            outside.append(e)
        else:
            inside.append(e)

    inside.sort(key=key, reverse=True)
    outside.sort(key=key)
    return inside + outside


def item_at_point(
    view: GtkView,
    pos: Pos,
    distance: float = 0.5,
    exclude: Sequence[Item] = (),
) -> Iterator[Item]:
    """Return the topmost item located at ``pos`` (x, y).

    Parameters:
        - view: a view
        - pos: Position, a tuple ``(x, y)`` in view coordinates
        - selected: if False returns first non-selected item
    """
    return (
        item for _d, item in order_items(item_distance(view, pos, distance, exclude))
    )
