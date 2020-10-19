"""Some Gaphor specific updates to the canvas. This is done by setting the
correct properties on gaphas' modules.

Matrix
------
Small utility class wrapping cairo.Matrix. The `Matrix` class adds
state preservation capabilities.
"""

from __future__ import annotations

from typing import Callable, Set, Tuple

import cairo

from gaphas.state import observed, reversible_method


class Matrix:
    """Matrix wrapper. This version sends @observed messages on state changes.

    >>> cairo.Matrix()
    cairo.Matrix(1, 0, 0, 1, 0, 0)
    >>> Matrix()
    Matrix(1, 0, 0, 1, 0, 0)
    """

    def __init__(self, xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0):
        self._matrix = cairo.Matrix(xx, yx, xy, yy, x0, y0)
        self._handlers: Set[Callable[[Matrix], None]] = set()

    def add_handler(self, handler: Callable[[Matrix], None]):
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Matrix], None]):
        self._handlers.discard(handler)

    def notify(self):
        for handler in self._handlers:
            handler(self)

    @observed
    def invert(self) -> None:
        self._matrix.invert()
        self.notify()

    @observed
    def rotate(self, radians: float) -> None:
        self._matrix.rotate(radians)
        self.notify()

    @observed
    def scale(self, sx, sy) -> None:
        self._matrix.scale(sx, sy)
        self.notify()

    @observed
    def translate(self, tx, ty) -> None:
        self._matrix.translate(tx, ty)
        self.notify()

    def multiply(self, m: cairo.Matrix) -> cairo.Matrix:
        return self._matrix.multiply(m)

    reversible_method(invert, invert)
    reversible_method(rotate, rotate, {"radians": lambda radians: -radians})
    reversible_method(scale, scale, {"sx": lambda sx: 1 / sx, "sy": lambda sy: 1 / sy})
    reversible_method(
        translate, translate, {"tx": lambda tx: -tx, "ty": lambda ty: -ty}
    )

    def transform_distance(self, dx, dy) -> Tuple[float, float]:
        return self._matrix.transform_distance(dx, dy)  # type: ignore[no-any-return]

    def transform_point(self, x, y) -> Tuple[float, float]:
        return self._matrix.transform_point(x, y)  # type: ignore[no-any-return]

    def inverse(self) -> Matrix:
        m = Matrix(*self._matrix)
        m.invert()
        return m

    def __eq__(self, other) -> bool:
        if isinstance(other, cairo.Matrix):
            return self._matrix.__eq__(other)  # type: ignore[no-any-return]
        else:
            return False

    def __ne__(self, other) -> bool:
        if isinstance(other, cairo.Matrix):
            return self._matrix.__ne__(other)  # type: ignore[no-any-return]
        else:
            return False

    def __getitem__(self, val: int) -> float:
        return self._matrix[val]  # type: ignore[index,no-any-return]

    def __mul__(self, other: cairo.Matrix) -> cairo.Matrix:
        return self._matrix.__mul__(other)  # type: ignore[operator,no-any-return]

    def __repr__(self):
        return f"Matrix{tuple(self._matrix)}"  # type: ignore[arg-type]
