"""
Basic connectors such as Ports and Handles.
"""

import functools
import warnings

from gaphas.constraint import LineConstraint, PositionConstraint
from gaphas.geometry import distance_line_point, distance_point_point
from gaphas.solver import NORMAL, solvable
from gaphas.state import observed, reversible_property


def deprecated(message, since):
    def _deprecated(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__}: {message}", category=DeprecationWarning, stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper

    return _deprecated


class Position:
    """
    A point constructed of two `Variable`'s.

    >>> vp = Position((3, 5))
    >>> vp.x, vp.y
    (Variable(3, 20), Variable(5, 20))
    >>> vp.pos
    (Variable(3, 20), Variable(5, 20))
    >>> vp[0], vp[1]
    (Variable(3, 20), Variable(5, 20))
    """

    x = solvable(varname="_v_x")
    y = solvable(varname="_v_y")

    def __init__(self, pos, strength=NORMAL):
        self.x, self.y = pos
        self.x.strength = strength
        self.y.strength = strength

    def _set_pos(self, pos):
        """
        Set handle position (Item coordinates).
        """
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

    def __str__(self):
        return f"<{self.__class__.__name__} object on ({self.x}, {self.y})>"

    __repr__ = __str__

    def __getitem__(self, index):
        """
        Shorthand for returning the x(0) or y(1) component of the point.

        >>> h = Position((3, 5))
        >>> h[0]
        Variable(3, 20)
        >>> h[1]
        Variable(5, 20)
        """
        return (self.x, self.y)[index]


class Handle:
    """
    Handles are used to support modifications of Items.

    If the handle is connected to an item, the ``connected_to``
    property should refer to the item. A ``disconnect`` handler should
    be provided that handles all disconnect behaviour (e.g. clean up
    constraints and ``connected_to``).

    Note for those of you that use the Pickle module to persist a
    canvas: The property ``disconnect`` should contain a callable
    object (with __call__() method), so the pickle handler can also
    pickle that. Pickle is not capable of pickling ``instancemethod``
    or ``function`` objects.
    """

    def __init__(self, pos=(0, 0), strength=NORMAL, connectable=False, movable=True):
        self._pos = Position(pos, strength)
        self._connectable = connectable
        self._movable = movable
        self._visible = True

    def _set_pos(self, pos):
        """
        Shortcut for ``handle.pos.pos = pos``

        >>> h = Handle((10, 10))
        >>> h.pos
        <Position object on (10, 10)>
        >>> h.pos = (20, 15)
        >>> h.pos
        <Position object on (20, 15)>
        """
        self._pos.pos = pos

    pos = property(lambda s: s._pos, _set_pos)

    @deprecated("Use Handle.pos", "1.1.0")
    def _set_x(self, x):
        """
        Shortcut for ``handle.pos.x = x``
        """
        self._pos.x = x

    @deprecated("Use Handle.pos.x", "1.1.0")
    def _get_x(self):
        return self._pos.x

    x = property(_get_x, _set_x)

    @deprecated("Use Handle.pos", "1.1.0")
    def _set_y(self, y):
        """
        Shortcut for ``handle.pos.y = y``
        """
        self._pos.y = y

    @deprecated("Use Handle.pos.y", "1.1.0")
    def _get_y(self):
        return self._pos.y

    y = property(_get_y, _set_y)

    @observed
    def _set_connectable(self, connectable):
        self._connectable = connectable

    connectable = reversible_property(lambda s: s._connectable, _set_connectable)

    @observed
    def _set_movable(self, movable):
        self._movable = movable

    movable = reversible_property(lambda s: s._movable, _set_movable)

    @observed
    def _set_visible(self, visible):
        self._visible = visible

    visible = reversible_property(lambda s: s._visible, _set_visible)

    def __str__(self):
        return f"<{self.__class__.__name__} object on ({self._pos.x}, {self._pos.y})>"

    __repr__ = __str__


class Port:
    """Port connectable part of an item.

    The Item's handle connects to a port.

    """

    def __init__(self):
        super().__init__()

        self._connectable = True

    @observed
    def _set_connectable(self, connectable):
        self._connectable = connectable

    connectable = reversible_property(lambda s: s._connectable, _set_connectable)

    def glue(self, pos):
        """
        Get glue point on the port and distance to the port.
        """
        raise NotImplemented("Glue method not implemented")

    def constraint(self, canvas, item, handle, glue_item):
        """
        Create connection constraint between item's handle and glue item.
        """
        raise NotImplemented("Constraint method not implemented")


class LinePort(Port):
    """
    Port defined as a line between two handles.
    """

    def __init__(self, start, end):
        super().__init__()

        self.start = start
        self.end = end

    def glue(self, pos):
        """
        Get glue point on the port and distance to the port.

        >>> p1, p2 = (0.0, 0.0), (100.0, 100.0)
        >>> port = LinePort(p1, p2)
        >>> port.glue((50, 50))
        ((50.0, 50.0), 0.0)
        >>> port.glue((0, 10))
        ((5.0, 5.0), 7.0710678118654755)
        """
        d, pl = distance_line_point(self.start, self.end, pos)
        return pl, d

    def constraint(self, canvas, item, handle, glue_item):
        """
        Create connection line constraint between item's handle and
        the port.
        """
        line = canvas.project(glue_item, self.start, self.end)
        point = canvas.project(item, handle.pos)
        return LineConstraint(line, point)


class PointPort(Port):
    """
    Port defined as a point.
    """

    def __init__(self, point):
        super().__init__()
        self.point = point

    def glue(self, pos):
        """
        Get glue point on the port and distance to the port.

        >>> h = Handle((10, 10))
        >>> port = PointPort(h.pos)
        >>> port.glue((10, 0))
        (<Position object on (10, 10)>, 10.0)
        """
        d = distance_point_point(self.point, pos)
        return self.point, d

    def constraint(self, canvas, item, handle, glue_item):
        """
        Return connection position constraint between item's handle
        and the port.
        """
        origin = canvas.project(glue_item, self.point)
        point = canvas.project(item, handle.pos)
        c = PositionConstraint(origin, point)
        return c  # PositionConstraint(origin, point)
