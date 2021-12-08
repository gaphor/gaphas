import logging
from functools import singledispatch
from typing import Iterable, Optional, Sequence

from gi.repository import Gdk, Gtk

from gaphas.connector import ConnectionSink, ConnectionSinkType, Connector
from gaphas.handle import Handle
from gaphas.item import Element, Item
from gaphas.types import Pos
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
        cinfo = model.connections.get_connection(self.handle)
        if cinfo:
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
    ) -> Optional[ConnectionSinkType]:
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

    def __init__(self, item: Item, handle: Handle, view: GtkView):
        super().__init__(item, handle, view)
        self.cursor: Optional[Gdk.Cursor] = None

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
            if Gtk.get_major_version() == 3:
                cursor = Gdk.Cursor.new_from_name(display, self.CURSORS[index])
                self.cursor = self.view.get_window().get_cursor()
                self.view.get_window().set_cursor(cursor)
            else:
                cursor = Gdk.Cursor.new_from_name(self.CURSORS[index])
                self.cursor = self.view.get_cursor()
                self.view.set_cursor(cursor)

    def reset_cursor(self) -> None:
        self.view.get_window().set_cursor(
            self.cursor
        ) if Gtk.get_major_version() == 3 else self.view.set_cursor(self.cursor)


# Maybe make this an iterator? so extra checks can be done on the item
def item_at_point(
    view: GtkView,
    pos: Pos,
    distance: float = 0.5,
    exclude: Sequence[Item] = (),
) -> Iterable[Item]:
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
        item_distance = item.point(ix, iy)
        if item_distance is None:
            log.warning("Item distance is None for %s", item)
            continue
        if item_distance < distance:
            yield item
