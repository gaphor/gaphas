"""Basic connectors such as Ports and Handles."""

from __future__ import annotations

from gaphas.position import Position
from gaphas.solver import NORMAL
from gaphas.types import Pos, SupportsFloatPos, TypedProperty


class Handle:
    """Handles are used to support modifications of Items.

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

    def __init__(
        self,
        pos: Pos = (0, 0),
        strength: int = NORMAL,
        connectable: bool = False,
        movable: bool = True,
    ) -> None:
        """Create a new handle.

        Position is in item  coordinates.
        """
        self._pos = Position(pos[0], pos[1], strength)
        self._connectable = connectable
        self._movable = movable
        self._visible = True
        self._glued = False

    def _set_pos(self, pos: Position | SupportsFloatPos) -> None:
        """
        Shortcut for ``handle.pos.pos = pos``

        >>> h = Handle((10, 10))
        >>> h.pos = (20, 15)
        >>> h.pos
        <Position object on (20, 15)>
        """
        self._pos.pos = pos

    pos: TypedProperty[Position, Position | SupportsFloatPos]
    pos = property(lambda s: s._pos, _set_pos, doc="The Handle's position")

    @property
    def connectable(self) -> bool:
        """Can this handle actually connectect to a port?"""
        return self._connectable

    @connectable.setter
    def connectable(self, connectable: bool) -> None:
        self._connectable = connectable

    @property
    def movable(self) -> bool:
        """Can this handle be moved by a mouse pointer?"""
        return self._movable

    @movable.setter
    def movable(self, movable: bool) -> None:
        self._movable = movable

    @property
    def visible(self) -> bool:
        """Is this handle visible to the user?"""
        return self._visible

    @visible.setter
    def visible(self, visible: bool) -> None:
        self._visible = visible

    @property
    def glued(self) -> bool:
        """Is the handle being moved and about to be connected?"""
        return self._glued

    @glued.setter
    def glued(self, glued: bool) -> None:
        self._glued = glued

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} object on ({self._pos.x}, {self._pos.y})>"

    __repr__ = __str__
