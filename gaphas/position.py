from gaphas.matrix import Matrix
from gaphas.solver import NORMAL, Constraint, Variable


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
        """
        Initialize a variable.

        Args:
            self: (todo): write your description
            x: (int): write your description
            y: (int): write your description
            strength: (float): write your description
            NORMAL: (todo): write your description
        """
        self._x = Variable(x, strength)
        self._y = Variable(y, strength)

    def _set_x(self, v):
        """
        Set the x and y.

        Args:
            self: (todo): write your description
            v: (todo): write your description
        """
        self._x.value = v

    x = property(lambda s: s._x, _set_x)

    def _set_y(self, v):
        """
        Set y value of the y

        Args:
            self: (todo): write your description
            v: (todo): write your description
        """
        self._y.value = v

    y = property(lambda s: s._y, _set_y)

    strength = property(lambda s: s._x.strength)

    def _set_pos(self, pos):
        """Set handle position (Item coordinates)."""
        self._x.value, self._y.value = pos

    pos = property(lambda s: (s._x, s._y), _set_pos)

    def __str__(self):
        """
        Return a string representation of this object.

        Args:
            self: (todo): write your description
        """
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
        """
        Return an iterator over all iterators.

        Args:
            self: (todo): write your description
        """
        return iter((self._x, self._y))

    def __eq__(self, other):
        """
        Determine whether two values are equal.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return isinstance(other, Position) and self.x == other.x and self.y == other.y


class MatrixProjection(Constraint):
    def __init__(self, pos: Position, matrix: Matrix):
        """
        Initialize the gradient.

        Args:
            self: (todo): write your description
            pos: (int): write your description
            matrix: (array): write your description
        """
        proj_pos = Position(0, 0, pos.strength)
        super().__init__(proj_pos.x, proj_pos.y, pos.x, pos.y)

        self._orig_pos = pos
        self._proj_pos = proj_pos
        self.matrix = matrix
        self.solve_for(self._proj_pos.x)

    def add_handler(self, handler):
        """
        Add a handler.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
        """
        if not self._handlers:
            self.matrix.add_handler(self._on_matrix_changed)
        super().add_handler(handler)

    def remove_handler(self, handler):
        """
        Removes a previously registered handler.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
        """
        super().remove_handler(handler)
        if not self._handlers:
            self.matrix.remove_handler(self._on_matrix_changed)

    def _set_x(self, x):
        """
        Set the x value at x.

        Args:
            self: (todo): write your description
            x: (todo): write your description
        """
        self._proj_pos.x = x

    def _set_y(self, y):
        """
        Sets the y - axis.

        Args:
            self: (todo): write your description
            y: (todo): write your description
        """
        self._proj_pos.y = y

    pos = property(lambda s: s._proj_pos)
    x = property(lambda s: s._proj_pos.x, _set_x)
    y = property(lambda s: s._proj_pos.y, _set_y)

    def mark_dirty(self, var):
        """
        Mark the given variable as closed.

        Args:
            self: (todo): write your description
            var: (array): write your description
        """
        if var is self._orig_pos.x or var is self._orig_pos.y:
            super().mark_dirty(self._orig_pos.x)
            super().mark_dirty(self._orig_pos.y)
        else:
            super().mark_dirty(self._proj_pos.x)
            super().mark_dirty(self._proj_pos.y)

    def solve_for(self, var):
        """
        Solve the linear system.

        Args:
            self: (todo): write your description
            var: (array): write your description
        """
        if var is self._orig_pos.x or var is self._orig_pos.y:
            self._orig_pos.x, self._orig_pos.y = self.matrix.inverse().transform_point(*self._proj_pos)  # type: ignore[misc]
        else:
            self._proj_pos.x, self._proj_pos.y = self.matrix.transform_point(*self._orig_pos)  # type: ignore[misc]

    def _on_matrix_changed(self, matrix):
        """
        Called when a new matrix changed.

        Args:
            self: (todo): write your description
            matrix: (todo): write your description
        """
        self.mark_dirty(self._orig_pos.x)
        self.notify()

    def __getitem__(self, index):
        """
        Return the item at the given index.

        Args:
            self: (todo): write your description
            index: (int): write your description
        """
        return self._proj_pos[index]
