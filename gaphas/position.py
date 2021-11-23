from __future__ import annotations

from typing import Callable, SupportsFloat

from gaphas.matrix import Matrix
from gaphas.solver import NORMAL, BaseConstraint, Variable
from gaphas.types import Pos, SupportsFloatPos, TypedProperty


class Position:
    """A point constructed of two `Variable`'s.

    >>> vp = Position(3, 5)
    >>> vp.x, vp.y
    (Variable(3, 20), Variable(5, 20))
    >>> vp.pos
    (Variable(3, 20), Variable(5, 20))
    >>> vp[0], vp[1]
    (Variable(3, 20), Variable(5, 20))
    """

    def __init__(self, x, y, strength=NORMAL):
        self._x = Variable(x, strength)
        self._y = Variable(y, strength)
        self._handlers: set[Callable[[Position, Pos], None]] = set()
        self._setting_pos = 0

    def add_handler(self, handler: Callable[[Position, Pos], None]) -> None:
        if not self._handlers:
            self._x.add_handler(self._propagate_x)
            self._y.add_handler(self._propagate_y)
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Position, Pos], None]) -> None:
        self._handlers.discard(handler)
        if not self._handlers:
            self._x.remove_handler(self._propagate_x)
            self._y.remove_handler(self._propagate_y)

    def notify(self, oldpos: Pos) -> None:
        for handler in self._handlers:
            handler(self, oldpos)

    def _propagate_x(self, variable, oldval):
        if not self._setting_pos:
            self.notify((oldval, self._y.value))

    def _propagate_y(self, variable, oldval):
        if not self._setting_pos:
            self.notify((self._x.value, oldval))

    @property
    def strength(self) -> int:
        """Strength."""
        return self._x.strength

    def _set_x(self, v: SupportsFloat) -> None:
        self._x.value = v

    x: TypedProperty[Variable, SupportsFloat]
    x = property(lambda s: s._x, _set_x, doc="Position.x")

    def _set_y(self, v: SupportsFloat) -> None:
        self._y.value = v

    y: TypedProperty[Variable, SupportsFloat]
    y = property(lambda s: s._y, _set_y, doc="Position.y")

    def _set_pos(self, pos: Position | SupportsFloatPos) -> None:
        """Set handle position (Item coordinates)."""
        oldpos = (self._x.value, self._y.value)
        self._setting_pos += 1
        try:
            self._x.value, self._y.value = pos
        finally:
            self._setting_pos -= 1
        self.notify(oldpos)

    pos: TypedProperty[tuple[Variable, Variable], Position | SupportsFloatPos]
    pos = property(lambda s: (s._x, s._y), _set_pos, doc="The position.")

    def tuple(self) -> tuple[float, float]:
        return (self._x.value, self._y.value)

    def __str__(self):
        return f"<{self.__class__.__name__} object on ({self._x}, {self._y})>"

    __repr__ = __str__

    def __getitem__(self, index):
        """Shorthand for returning the x(0) or y(1) component of the point.

        >>> h = Position(3, 5)
        >>> h[0]
        Variable(3, 20)
        >>> h[1]
        Variable(5, 20)
        """
        return (self._x, self._y)[index]

    def __iter__(self):
        return iter((self._x, self._y))

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y


class MatrixProjection(BaseConstraint):
    def __init__(self, pos: Position, matrix: Matrix):
        proj_pos = Position(0, 0, pos.strength)
        super().__init__(proj_pos.x, proj_pos.y, pos.x, pos.y)

        self._orig_pos = pos
        self._proj_pos = proj_pos
        self.matrix = matrix
        self.solve_for(self._proj_pos.x)

    def add_handler(self, handler):
        """Add a callback handler."""
        if not self._handlers:
            self.matrix.add_handler(self._on_matrix_changed)
        super().add_handler(handler)

    def remove_handler(self, handler):
        """Remove a previously assigned handler."""
        super().remove_handler(handler)
        if not self._handlers:
            self.matrix.remove_handler(self._on_matrix_changed)

    @property
    def pos(self) -> Position:
        """The projected position."""
        return self._proj_pos

    def _set_x(self, x):
        self._proj_pos.x = x

    x: TypedProperty[Variable, SupportsFloat]
    x = property(
        lambda s: s._proj_pos.x, _set_x, doc="The projected position's ``x`` part."
    )

    def _set_y(self, y):
        self._proj_pos.y = y

    y: TypedProperty[Variable, SupportsFloat]
    y = property(
        lambda s: s._proj_pos.y, _set_y, doc="The projected position's ``y`` part."
    )

    def mark_dirty(self, var):
        if var is self._orig_pos.x or var is self._orig_pos.y:
            super().mark_dirty(self._orig_pos.x)
            super().mark_dirty(self._orig_pos.y)
        else:
            super().mark_dirty(self._proj_pos.x)
            super().mark_dirty(self._proj_pos.y)

    def solve_for(self, var):
        if var is self._orig_pos.x or var is self._orig_pos.y:
            self._orig_pos.x, self._orig_pos.y = self.matrix.inverse().transform_point(
                *self._proj_pos
            )
        else:
            self._proj_pos.x, self._proj_pos.y = self.matrix.transform_point(
                *self._orig_pos
            )

    def _on_matrix_changed(self, matrix, _orig):
        self.mark_dirty(self._orig_pos.x)
        self.notify()

    def __getitem__(self, index):
        return self._proj_pos[index]
