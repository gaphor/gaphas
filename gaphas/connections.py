"""This module contains a connections manager."""

from collections import namedtuple
from typing import Optional

from gaphas import table
from gaphas.solver import Solver
from gaphas.state import observed, reversible_method, reversible_pair

#
# Information about two connected items
#
# - item: connecting item
# - handle: handle of connecting item (points connected item)
# - connected: connected item
# - port: port of connected item
# - constraint: optional connection constraint
# - callback: optional disconnection callback
#
Connection = namedtuple("Connection", "item handle connected port constraint callback")


class ConnectionError(Exception):
    """Exception raised when there is an error when connecting an items with
    each other."""


class Connections:
    def __init__(self, solver: Optional[Solver] = None):
        self._solver = solver or Solver()
        self._connections = table.Table(Connection, list(range(4)))

    solver = property(lambda s: s._solver)

    def solve(self):
        self._solver.solve()

    def add_constraint(self, item, constraint):
        self._solver.add_constraint(constraint)
        self._connections.insert(item, None, None, None, constraint, None)
        return constraint

    def remove_constraint(self, item, constraint):
        self._solver.remove_constraint(constraint)
        self._connections.delete(item, None, None, None, constraint, None)

    @observed
    def connect_item(
        self, item, handle, connected, port, constraint=None, callback=None
    ):
        """Create a connection between two items. The connection is registered
        and the constraint is added to the constraint solver.

        The pair (item, handle) should be unique and not yet connected.

        The callback is invoked when the connection is broken.

        :Parameters:
         item
            Connecting item (i.e. a line).
         handle
            Handle of connecting item.
         connected
            Connected item (i.e. a box).
         port
            Port of connected item.
         constraint
            Constraint to keep the connection in place.
         callback
            Function to be called on disconnection.

        ConnectionError is raised in case handle is already registered
        on a connection.
        """
        if self.get_connection(handle):
            raise ConnectionError(
                f"Handle {handle} of item {item} is already connected"
            )

        self._connections.insert(item, handle, connected, port, constraint, callback)

        if constraint:
            self._solver.add_constraint(constraint)

    def disconnect_item(self, item, handle=None):
        """Disconnect the connections of an item.

        If handle is not None, only the connection for that handle is
        disconnected.
        """
        # disconnect on canvas level
        for cinfo in list(self._connections.query(item=item, handle=handle)):
            self._disconnect_item(*cinfo)

    @observed
    def _disconnect_item(self, item, handle, connected, port, constraint, callback):
        """Perform the real disconnect."""
        # Same arguments as connect_item, makes reverser easy
        if constraint:
            self._solver.remove_constraint(constraint)

        if callback:
            callback()

        self._connections.delete(item, handle, connected, port, constraint, callback)

    reversible_pair(connect_item, _disconnect_item)

    def remove_connections_to_item(self, item):
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

    @observed
    def reconnect_item(self, item, handle, port=None, constraint=None):
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

    reversible_method(
        reconnect_item,
        reverse=reconnect_item,
        bind={
            "port": lambda self, item, handle: self.get_connection(handle).port,
            "constraint": lambda self, item, handle: self.get_connection(
                handle
            ).constraint,
        },
    )

    def get_connection(self, handle):
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

    def get_connections(self, item=None, handle=None, connected=None, port=None):
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
