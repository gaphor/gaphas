from functools import singledispatch
from typing import Callable, Optional

from typing_extensions import Protocol

from gaphas.connections import Connections
from gaphas.connector import Handle, Port
from gaphas.item import Item, matrix_i2i
from gaphas.types import Pos


class ConnectionSinkType(Protocol):
    item: Item
    port: Port

    def __init__(self, item: Item, port: Port):
        ...

    def find_port(self, pos: Pos) -> Optional[Port]:
        ...


class ItemConnector:
    """Connect or disconnect an item's handle to another item or port."""

    GLUE_DISTANCE = 10  # Glue distance in view points

    def __init__(self, item: Item, handle: Handle, connections: Connections):
        self.item = item
        self.handle = handle
        self.connections = connections

    def allow(self, sink: ConnectionSinkType) -> bool:
        return True

    def glue(self, sink: ConnectionSinkType) -> None:
        """Glue the Connector handle on the sink's port."""
        handle = self.handle
        item = self.item
        matrix = matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        gluepos, dist = sink.port.glue(pos)
        matrix.invert()
        handle.pos = matrix.transform_point(*gluepos)

    def connect(self, sink: ConnectionSinkType) -> None:
        """Connect the handle to a sink (item, port).

        Note that connect() also takes care of disconnecting in case a
        handle is reattached to another element.
        """

        cinfo = self.connections.get_connection(self.handle)

        # Already connected? disconnect first.
        if cinfo:
            self.disconnect()

        if not self.allow(sink):
            return

        self.glue(sink)

        self.connect_handle(sink)

    def connect_handle(
        self, sink: ConnectionSinkType, callback: Optional[Callable[[], None]] = None
    ) -> None:
        """Create constraint between handle of a line and port of connectable
        item.

        :Parameters:
         sink
            Connectable item and port.
         callback
            Function to be called on disconnection.
        """
        handle = self.handle
        item = self.item

        constraint = sink.port.constraint(item, handle, sink.item)

        self.connections.connect_item(
            item, handle, sink.item, sink.port, constraint, callback=callback
        )

    def disconnect(self) -> None:
        """Disconnect the handle from the attached element."""
        self.connections.disconnect_item(self.item, self.handle)


Connector = singledispatch(ItemConnector)


class ItemConnectionSink:
    """Makes an item a sink.

    A sink is another item that an item's handle is connected to like a
    connectable item or port.
    """

    def __init__(self, item: Item, port: Port):
        self.item = item
        self.port = port

    def find_port(self, pos: Pos) -> Optional[Port]:
        """Glue to the closest item on the canvas.

        If the item can connect, it returns a port.
        """
        port = None
        max_dist = 10e6
        for p in self.item.ports():
            pg, d = p.glue(pos)
            if d >= max_dist:
                continue
            port = p
            max_dist = d

        return port


ConnectionSink = singledispatch(ItemConnectionSink)
