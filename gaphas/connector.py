from __future__ import annotations

from functools import singledispatch
from typing import Callable, Protocol

from gaphas.connections import Connections
from gaphas.geometry import intersect_line_line
from gaphas.handle import Handle
from gaphas.item import Element, Item, Line, matrix_i2i
from gaphas.port import LinePort, PointPort, Port  # noqa F401
from gaphas.position import Position  # noqa F401
from gaphas.solver import Constraint
from gaphas.types import Pos, SupportsFloatPos


class ConnectionSinkType(Protocol):
    item: Item
    port: Port | None

    def __init__(self, item: Item, distance: float = 10): ...

    def glue(
        self, pos: SupportsFloatPos, secondary_pos: SupportsFloatPos | None = None
    ) -> Pos | None: ...

    def constraint(self, item: Item, handle: Handle) -> Constraint: ...


class ItemConnector:
    """Connect or disconnect an item's handle to another item or port."""

    GLUE_DISTANCE = 10  # Glue distance in view points

    def __init__(self, item: Item, handle: Handle, connections: Connections):
        self.item = item
        self.handle = handle
        self.connections = connections

    def allow(self, sink):
        return True

    def secondary_handle(self) -> Handle | None:
        return None

    def glue(self, sink: ConnectionSinkType) -> Pos | None:
        """Glue the Connector handle on the sink's port."""
        handle = self.handle
        item = self.item
        matrix = matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        secondary_handle = self.secondary_handle()
        secondary_pos = (
            matrix.transform_point(*secondary_handle.pos) if secondary_handle else None
        )
        glue_pos = sink.glue(pos, secondary_pos)
        if glue_pos and self.allow(sink):
            matrix.invert()
            new_pos = matrix.transform_point(*glue_pos)
            handle.pos = new_pos
            return new_pos
        return None

    def connect(self, sink: ConnectionSinkType) -> None:
        """Connect the handle to a sink (item, port).

        Note that connect() also takes care of disconnecting in case a
        handle is reattached to another element.
        """

        # Already connected? disconnect first.
        if self.connections.get_connection(self.handle):
            self.disconnect()

        if not self.glue(sink):
            return

        self.connect_handle(sink)

    def connect_handle(
        self,
        sink: ConnectionSinkType,
        callback: Callable[[Item, Handle, Item, Port], None] | None = None,
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
    def secondary_handle(self) -> Handle | None:
        item = self.item
        handle = self.handle
        handles = item.handles()
        if len(handles) < 2:
            return None
        if handle is handles[0]:
            return handles[1]
        return handles[-2] if handle is handles[-1] else None


class ItemConnectionSink:
    """Makes an item a sink.

    A sink is another item that an item's handle is connected to like a
    connectable item or port.
    """

    def __init__(self, item: Item, distance: float = 10) -> None:
        self.item = item
        self.distance = distance
        self.port: Port | None = None

    def glue(
        self, pos: SupportsFloatPos, secondary_pos: SupportsFloatPos | None = None
    ) -> Pos | None:
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
        return glue_pos

    def constraint(self, item: Item, handle: Handle) -> Constraint:
        assert self.port, "constraint() can only be called after glue()"
        return self.port.constraint(item, handle, self.item)


ConnectionSink = singledispatch(ItemConnectionSink)


@ConnectionSink.register(Element)
class ElementConnectionSink(ItemConnectionSink):
    def glue(
        self, pos: SupportsFloatPos, secondary_pos: SupportsFloatPos | None = None
    ) -> Pos | None:
        if glue_pos := super().glue(pos, secondary_pos):
            return glue_pos

        if secondary_pos:
            for p in self.item.ports()[:4]:
                assert isinstance(p, LinePort)
                if point_on_line := intersect_line_line(
                    pos,  # type: ignore[arg-type]
                    secondary_pos,  # type: ignore[arg-type]
                    p.start,  # type: ignore[arg-type]
                    p.end,  # type: ignore[arg-type]
                ):
                    return point_on_line

        return None
