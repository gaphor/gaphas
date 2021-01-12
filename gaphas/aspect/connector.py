from functools import singledispatch
from typing import Callable, Optional, Tuple

from typing_extensions import Protocol

from gaphas.connections import Connections
from gaphas.connector import Handle, LinePort, Port
from gaphas.geometry import intersect_line_line
from gaphas.item import Element, Item, Line, matrix_i2i
from gaphas.solver import Constraint
from gaphas.types import Pos, SupportsFloatPos


class ConnectionSinkType(Protocol):
    item: Item
    port: Optional[Port]

    def __init__(self, item: Item, distance: float = 10):
        ...

    def glue(
        self, pos: SupportsFloatPos, secondary_pos: Optional[SupportsFloatPos] = None
    ) -> Tuple[Optional[Pos], float]:
        ...

    def constraint(self, item: Item, handle: Handle) -> Constraint:
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

    def secondary_handle(self) -> Optional[Handle]:
        return None

    def glue(self, sink: ConnectionSinkType) -> None:
        """Glue the Connector handle on the sink's port."""
        handle = self.handle
        item = self.item
        matrix = matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        secondary_handle = self.secondary_handle()
        secondary_pos = (
            matrix.transform_point(*secondary_handle.pos) if secondary_handle else None
        )
        gluepos, dist = sink.glue(pos, secondary_pos)
        if gluepos:
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

        constraint = sink.constraint(item, handle)

        self.connections.connect_item(
            item, handle, sink.item, sink.port, constraint, callback=callback
        )

    def disconnect(self) -> None:
        """Disconnect the handle from the attached element."""
        self.connections.disconnect_item(self.item, self.handle)


Connector = singledispatch(ItemConnector)


@Connector.register(Line)
class LineConnector(ItemConnector):
    def secondary_handle(self) -> Optional[Handle]:
        item = self.item
        handle = self.handle
        handles = item.handles()
        if len(handles) < 2:
            return None
        if handle is handles[0]:
            return handles[1]
        if handle is handles[-1]:
            return handles[-2]
        return None


class ItemConnectionSink:
    """Makes an item a sink.

    A sink is another item that an item's handle is connected to like a
    connectable item or port.
    """

    def __init__(self, item: Item, distance: float = 10) -> None:
        self.item = item
        self.distance = distance
        self.port: Optional[Port] = None

    def glue(
        self, pos: SupportsFloatPos, secondary_pos: Optional[SupportsFloatPos] = None
    ) -> Tuple[Optional[Pos], float]:
        max_dist = self.distance
        glue_pos = None
        for p in self.item.ports():
            if not p.connectable:
                continue

            g, d = p.glue(pos)

            if d < max_dist:
                max_dist = d
                self.port = p
                glue_pos = g
        return glue_pos, max_dist if glue_pos else 1e4

    def constraint(self, item: Item, handle: Handle) -> Constraint:
        assert self.port, "constraint() can only be called after glue()"
        return self.port.constraint(item, handle, self.item)


ConnectionSink = singledispatch(ItemConnectionSink)


@ConnectionSink.register(Element)
class ElementConnectionSink(ItemConnectionSink):
    def glue(
        self, pos: SupportsFloatPos, secondary_pos: Optional[SupportsFloatPos] = None
    ) -> Tuple[Optional[Pos], float]:
        glue_pos, dist = super().glue(pos, secondary_pos)
        if glue_pos:
            return glue_pos, dist

        if secondary_pos:
            for p in self.item.ports()[:4]:
                assert isinstance(p, LinePort)
                point_on_line = intersect_line_line(
                    pos, secondary_pos, p.start, p.end  # type: ignore[arg-type]
                )
                if point_on_line:
                    return point_on_line, 0

        return None, 1e4
