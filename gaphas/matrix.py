"""Some Gaphor specific updates to the canvas. This is done by setting the
correct properties on gaphas' modules.

Matrix
------
Small utility class wrapping cairo.Matrix. The `Matrix` class adds
state preservation capabilities.
"""

from __future__ import annotations

from typing import Callable, Optional, Set, Tuple

import cairo

from gaphas.state import observed, reversible_method


class Matrix:
    """Matrix wrapper. This version sends @observed messages on state changes.

    >>> Matrix()
    Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    """

    def __init__(
        self,
        xx=1.0,
        yx=0.0,
        xy=0.0,
        yy=1.0,
        x0=0.0,
        y0=0.0,
        matrix: Optional[cairo.Matrix] = None,
    ):
        """
        Initializes the matrix.

        Args:
            self: (todo): write your description
            xx: (int): write your description
            yx: (int): write your description
            xy: (int): write your description
            yy: (int): write your description
            x0: (float): write your description
            y0: (array): write your description
            matrix: (array): write your description
            Optional: (todo): write your description
            cairo: (todo): write your description
            Matrix: (array): write your description
        """
        self._matrix = matrix or cairo.Matrix(xx, yx, xy, yy, x0, y0)
        self._handlers: Set[Callable[[Matrix], None]] = set()

    def add_handler(self, handler: Callable[[Matrix], None]):
        """
        Add a new handler.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
            Callable: (todo): write your description
            Matrix: (array): write your description
        """
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Matrix], None]):
        """
        Removes a previously added handler.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
            Callable: (str): write your description
            Matrix: (array): write your description
        """
        self._handlers.discard(handler)

    def notify(self):
        """
        Call all registered handlers.

        Args:
            self: (todo): write your description
        """
        for handler in self._handlers:
            handler(self)

    @observed
    def invert(self) -> None:
        """
        Invert the matrix.

        Args:
            self: (todo): write your description
        """
        self._matrix.invert()
        self.notify()

    @observed
    def rotate(self, radians: float) -> None:
        """
        Rotate the matrix by the given angle.

        Args:
            self: (todo): write your description
            radians: (int): write your description
        """
        self._matrix.rotate(radians)
        self.notify()

    @observed
    def scale(self, sx, sy) -> None:
        """
        Scale the matrix.

        Args:
            self: (todo): write your description
            sx: (todo): write your description
            sy: (todo): write your description
        """
        self._matrix.scale(sx, sy)
        self.notify()

    @observed
    def translate(self, tx, ty) -> None:
        """
        Translate a transaction.

        Args:
            self: (todo): write your description
            tx: (todo): write your description
            ty: (array): write your description
        """
        self._matrix.translate(tx, ty)
        self.notify()

    @observed
    def set(self, xx=None, yx=None, xy=None, yy=None, x0=None, y0=None) -> None:
        """
        Set the color.

        Args:
            self: (todo): write your description
            xx: (dict): write your description
            yx: (dict): write your description
            xy: (dict): write your description
            yy: (dict): write your description
            x0: (array): write your description
            y0: (dict): write your description
        """
        updated = False
        m = self._matrix
        for name, val in (
            ("xx", xx),
            ("yx", yx),
            ("xy", xy),
            ("yy", yy),
            ("x0", x0),
            ("y0", y0),
        ):
            if val is not None and val != getattr(m, name):
                setattr(m, name, val)
                updated = True
        if updated:
            self.notify()

    # TODO: Make reversible
    reversible_method(invert, invert)
    reversible_method(rotate, rotate, {"radians": lambda radians: -radians})
    reversible_method(scale, scale, {"sx": lambda sx: 1 / sx, "sy": lambda sy: 1 / sy})
    reversible_method(
        translate, translate, {"tx": lambda tx: -tx, "ty": lambda ty: -ty}
    )

    def multiply(self, m: Matrix) -> Matrix:
        """
        Multiply the matrix.

        Args:
            self: (todo): write your description
            m: (array): write your description
        """
        return Matrix(matrix=self._matrix.multiply(m._matrix))

    def transform_distance(self, dx, dy) -> Tuple[float, float]:
        """
        Compute distance matrix.

        Args:
            self: (todo): write your description
            dx: (array): write your description
            dy: (array): write your description
        """
        return self._matrix.transform_distance(dx, dy)  # type: ignore[no-any-return]

    def transform_point(self, x, y) -> Tuple[float, float]:
        """
        Return a point x y to the image.

        Args:
            self: (todo): write your description
            x: (array): write your description
            y: (array): write your description
        """
        return self._matrix.transform_point(x, y)  # type: ignore[no-any-return]

    def inverse(self) -> Matrix:
        """
        Return the inverse of the matrix.

        Args:
            self: (todo): write your description
        """
        m = Matrix(matrix=cairo.Matrix(*self._matrix))  # type: ignore[misc]
        m.invert()
        return m

    def to_cairo(self):
        """
        Convert the rotation matrix.

        Args:
            self: (todo): write your description
        """
        return self._matrix

    def __eq__(self, other):
        """
        Determine if the matrix is equal.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        if isinstance(other, Matrix):
            return self._matrix == other._matrix
        else:
            return False

    def __ne__(self, other):
        """
        Returns true if this matrix are equal.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        if isinstance(other, Matrix):
            return self._matrix != other._matrix
        else:
            return False

    def __getitem__(self, val: int) -> float:
        """
        Get the value from the cache.

        Args:
            self: (todo): write your description
            val: (todo): write your description
        """
        return self._matrix[val]  # type: ignore[index,no-any-return]

    def __mul__(self, other: Matrix) -> Matrix:
        """
        Return a new matrix that is the current matrix.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return Matrix(matrix=self._matrix * other._matrix)

    def __repr__(self):
        """
        Return a repr representation of a repr__.

        Args:
            self: (todo): write your description
        """
        return f"Matrix{tuple(self._matrix)}"  # type: ignore[arg-type]
