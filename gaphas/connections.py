"""This module contains a connections manager."""

from __future__ import annotations

from typing import Callable, Iterator, NamedTuple

from gaphas import table
from gaphas.constraint import Constraint
from gaphas.handle import Handle
from gaphas.item import Item
from gaphas.port import Port
from gaphas.solver import Solver


class Connection(NamedTuple):
    """Information about two connected items.

    - item: connecting item
    - handle: handle of connecting item (points connected item)
    - connected: connected item
    - port: port of connected item
    - constraint: optional connection constraint
    - callback: optional disconnection callback
    """

    item: Item
    handle: Handle
    connected: Item
    port: Port
    constraint: Constraint
    callback: Callable[[Item, Handle, Item, Port], None]


class ConnectionError(Exception):
    """Exception raised when there is an error when connecting an items with
    each other."""


class Connections:
    """Manage connections and constraints."""

    def __init__(self, solver: Solver | None = None) -> None:
        self._solver = solver or Solver()
        self._connections: table.Table[Connection] = table.Table(
            Connection, tuple(range(5))
        )
        self._handlers: set[Callable[[Connection], None]] = set()

        self._solver.add_handler(self._on_constraint_solved)

    def add_handler(self, handler):
        """Add a callback handler.

        Handlers are triggered when a constraint has been solved.
        """
        self._handlers.add(handler)

    def remove_handler(self, handler):
        """Remove a previously assigned handler."""
        self._handlers.discard(handler)

    def _on_constraint_solved(self, constraint):
        for cinfo in self._connections.query(constraint=constraint):
            for handler in self._handlers:
                handler(cinfo)

    @property
    def solver(self) -> Solver:
        """The solver used by this connections instance."""
        return self._solver

    def solve(self) -> None:
        """Solve all constraints."""
        self._solver.solve()

    def add_constraint(self, item: Item, constraint: Constraint) -> Constraint:
        """Add a "simple" constraint for an item."""
        self._solver.add_constraint(constraint)
        self._connections.insert(item, None, None, None, constraint, None)
        return constraint

    def remove_constraint(self, item: Item, constraint: Constraint) -> None:
        """Remove an item specific constraint."""
        self._solver.remove_constraint(constraint)
        self._connections.delete(item, None, None, None, constraint, None)

    def connect_item(
        self,
        item: Item,
        handle: Handle,
        connected: Item,
        port: Port | None,
        constraint: Constraint | None = None,
        callback: Callable[[Item, Handle, Item, Port], None] | None = None,
    ) -> None:
        """Create a connection between two items. The connection is registered
        and the constraint is added to the constraint solver.

        The pair ``(item, handle)`` should be unique and not yet connected.

        The callback is invoked when the connection is broken.

        Args:
          item (Item): Connecting item (i.e. a line).
          handle (Handle): Handle of connecting item.
          connected (Item): Connected item (i.e. a box).
          port (Port): Port of connected item.
          constraint (Constraint): Constraint to keep the connection in place.
          callback (() -> None): Function to be called on disconnection.

        ``ConnectionError`` is raised in case handle is already registered
        on a connection.
        """
        if self.get_connection(handle):
            raise ConnectionError(
                f"Handle {handle} of item {item} is already connected"
            )

        self._connections.insert(item, handle, connected, port, constraint, callback)

        if constraint:
            self._solver.add_constraint(constraint)

    def disconnect_item(self, item: Item, handle: Handle | None = None) -> None:
        """Disconnect the connections of an item.

        If handle is not None, only the connection for that handle is
        disconnected.
        """
        for cinfo in list(self._connections.query(item=item, handle=handle)):
            self._disconnect_item(*cinfo)

    def _disconnect_item(
        self,
        item: Item,
        handle: Handle,
        connected: Item,
        port: Port,
        constraint: Constraint,
        callback: Callable[[Item, Handle, Item, Port], None],
    ) -> None:
        """Perform the real disconnect."""
        # Same arguments as connect_item, makes reverser easy
        if constraint:
            self._solver.remove_constraint(constraint)

        if callback is not None:
            callback(item, handle, connected, port)

        self._connections.delete(item, handle, connected, port, constraint, callback)

    def remove_connections_to_item(self, item: Item) -> None:
        """Remove all connections (handles connected to and constraints) for a
        specific item (to and from the item).

        This is some brute force cleanup (e.g. if constraints are
        referenced by items, those references are not cleaned up).
        """
        disconnect_item = self._disconnect_item
        # remove connections from this item
        for cinfo in list(self._connections.query(item=item)):
            disconnect_item(*cinfo)
        # remove constraints to this item
        for cinfo in list(self._connections.query(connected=item)):
            disconnect_item(*cinfo)

    def reconnect_item(
        self,
        item: Item,
        handle: Handle,
        port: Port | None = None,
        constraint: Constraint | None = None,
    ) -> None:
        """Update an existing connection.

        This is used to provide a new constraint to the connection.
        ``item`` and ``handle`` are the keys to the to-be-updated
        connection.
        """
        cinfo = self.get_connection(handle)
        if not cinfo:
            raise ValueError(
                f'No data available for item "{item}" and handle "{handle}"'
            )

        if cinfo.constraint:
            self._solver.remove_constraint(cinfo.constraint)
        self._connections.delete(item=cinfo.item, handle=cinfo.handle)

        self._connections.insert(
            item,
            handle,
            cinfo.connected,
            port or cinfo.port,
            constraint,
            cinfo.callback,
        )
        if constraint:
            self._solver.add_constraint(constraint)

    def get_connection(self, handle: Handle) -> Connection | None:
        """Get connection information for specified handle.

        >>> c = Connections()
        >>> from gaphas.item import Line
        >>> line = Line()
        >>> from gaphas import item
        >>> i = item.Line()
        >>> ii = item.Line()
        >>> c.connect_item(i, i.handles()[0], ii, ii.ports()[0])
        >>> c.get_connection(i.handles()[0])     # doctest: +ELLIPSIS
        Connection(item=<gaphas.item.Line object at 0x...)
        >>> c.get_connection(i.handles()[1])     # doctest: +ELLIPSIS
        >>> c.get_connection(ii.handles()[0])    # doctest: +ELLIPSIS
        """
        try:
            return next(self._connections.query(handle=handle))
        except StopIteration:
            return None

    def get_connections(
        self,
        item: Item | None = None,
        handle: Handle | None = None,
        connected: Item | None = None,
        port: Port | None = None,
    ) -> Iterator[Connection]:
        """Return an iterator of connection information.

        The list contains (item, handle). As a result an item may be
        in the list more than once (depending on the number of handles
        that are connected). If ``item`` is connected to itself it
        will also appear in the list.

        >>> c = Connections()
        >>> from gaphas import item
        >>> i = item.Line()
        >>> ii = item.Line()
        >>> iii = item.Line()
        >>> c.connect_item(i, i.handles()[0], ii, ii.ports()[0], None)

        >>> list(c.get_connections(item=i)) # doctest: +ELLIPSIS
        [Connection(item=<gaphas.item.Line object at 0x...]
        >>> list(c.get_connections(connected=i))
        []
        >>> list(c.get_connections(connected=ii)) # doctest: +ELLIPSIS
        [Connection(item=<gaphas.item.Line object at 0x...]

        >>> c.connect_item(ii, ii.handles()[0], iii, iii.ports()[0], None)
        >>> list(c.get_connections(item=ii)) # doctest: +ELLIPSIS
        [Connection(item=<gaphas.item.Line object at 0x...]
        >>> list(c.get_connections(connected=iii)) # doctest: +ELLIPSIS
        [Connection(item=<gaphas.item.Line object at 0x...]
        """
        return self._connections.query(
            item=item, handle=handle, connected=connected, port=port
        )
