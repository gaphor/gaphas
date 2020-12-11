from functools import singledispatch
from typing import Optional, Sequence, Tuple, Union

from gi.repository import Gdk

from gaphas.aspect.connector import ConnectionSink, ConnectionSinkType, Connector
from gaphas.connector import Handle, Port
from gaphas.item import Element, Item
from gaphas.types import Pos
from gaphas.view import DEFAULT_CURSOR, GtkView


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
        cinfo = model.connections.get_connection(self.handle)
        if cinfo:
            model.connections.solver.remove_constraint(cinfo.constraint)

    def move(self, pos: Pos) -> None:
        item = self.item
        view = self.view
        assert view.model

        v2i = view.get_matrix_v2i(item)

        x, y = v2i.transform_point(*pos)

        self.handle.pos = (x, y)

        self.glue(pos)

        # do not request matrix update as matrix recalculation will be
        # performed due to item normalization if required
        view.model.request_update(item, matrix=False)

    def stop_move(self, pos: Pos) -> None:
        self.connect(pos)

    def glue(
        self, pos: Pos, distance: int = GLUE_DISTANCE
    ) -> Optional[ConnectionSinkType]:
        """Glue to an item near a specific point.

        Returns a ConnectionSink or None.
        """
        item = self.item
        handle = self.handle
        view = self.view

        if not handle.connectable:
            return None

        connectable, port, glue_pos = port_at_point(
            view, pos, distance=distance, exclude=(item,)
        )

        # check if item and found item can be connected on closest port
        if connectable and port and glue_pos:
            model = self.view.model
            assert model
            connections = model.connections
            connector = Connector(self.item, self.handle, connections)
            sink = ConnectionSink(connectable, port)

            if connector.allow(sink):
                # transform coordinates from view space to the item
                # space and update position of item's handle
                v2i = view.get_matrix_v2i(item).transform_point
                handle.pos = v2i(*glue_pos)
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

        # find connectable item and its port
        sink = self.glue(pos)

        # no new connectable item, then diconnect and exit
        if sink:
            connector.connect(sink)
        else:
            cinfo = connections.get_connection(handle)
            if cinfo:
                connector.disconnect()

        model.request_update(self.item)


HandleMove = singledispatch(ItemHandleMove)


@HandleMove.register(Element)
class ElementHandleMove(ItemHandleMove):
    CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")

    def start_move(self, pos: Pos) -> None:
        super().start_move(pos)
        self.set_cursor()

    def stop_move(self, pos: Pos) -> None:
        self.reset_cursor()
        super().stop_move(pos)

    def set_cursor(self) -> None:
        index = self.item.handles().index(self.handle)
        if index < 4:
            display = self.view.get_display()
            cursor = Gdk.Cursor.new_from_name(display, self.CURSORS[index])
            self.view.get_window().set_cursor(cursor)

    def reset_cursor(self) -> None:
        cursor = Gdk.Cursor(DEFAULT_CURSOR)
        self.view.get_window().set_cursor(cursor)


def port_at_point(
    view: GtkView, vpos: Pos, distance: float = 10, exclude: Sequence[Item] = (),
) -> Union[Tuple[Item, Port, Tuple[float, float]], Tuple[None, None, None]]:
    """Find item with port closest to specified position.

    List of items to be ignored can be specified with `exclude`
    parameter.

    Tuple is returned

    - found item
    - closest, connectable port
    - closest point on found port (in view coordinates)

    :Parameters:
        vpos
        Position specified in view coordinates.
        distance
        Max distance from point to a port (default 10)
        exclude
        Set of items to ignore.
    """
    v2i = view.get_matrix_v2i
    vx, vy = vpos

    max_dist = distance
    port = None
    glue_pos = None
    item = None

    rect = (vx - distance, vy - distance, distance * 2, distance * 2)
    for i in reversed(list(view.get_items_in_rectangle(rect))):
        if i in exclude:
            continue
        for p in i.ports():
            if not p.connectable:
                continue

            ix, iy = v2i(i).transform_point(vx, vy)
            pg, d = p.glue((ix, iy))

            if d >= max_dist:
                continue

            max_dist = d
            item = i
            port = p

            # transform coordinates from connectable item space to view
            # space
            i2v = view.get_matrix_i2v(i).transform_point
            glue_pos = i2v(*pg)
    return item, port, glue_pos  # type: ignore[return-value]
