"""Some Gaphor specific updates to the canvas. This is done by setting the
correct properties on gaphas' modules.

Matrix
------
Small utility class wrapping cairo.Matrix. The `Matrix` class adds
state notification capabilities.
"""

from __future__ import annotations

from typing import Callable, SupportsFloat

import cairo

Matrixtuple = tuple[float, float, float, float, float, float]


class Matrix:
    """Matrix wrapper.

    >>> Matrix()
    Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    """

    def __init__(
        self,
        xx: float = 1.0,
        yx: float = 0.0,
        xy: float = 0.0,
        yy: float = 1.0,
        x0: float = 0.0,
        y0: float = 0.0,
        matrix: cairo.Matrix | None = None,
    ) -> None:
        self._matrix = matrix or cairo.Matrix(xx, yx, xy, yy, x0, y0)
        self._handlers: set[Callable[[Matrix, Matrixtuple], None]] = set()

    def add_handler(
        self,
        handler: Callable[[Matrix, Matrixtuple], None],
    ) -> None:
        self._handlers.add(handler)

    def remove_handler(
        self,
        handler: Callable[[Matrix, Matrixtuple], None],
    ) -> None:
        self._handlers.discard(handler)

    def notify(self, old: Matrixtuple) -> None:
        for handler in self._handlers:
            handler(self, old)

    def invert(self) -> None:
        old: Matrixtuple = self.tuple()
        self._matrix.invert()
        self.notify(old)

    def rotate(self, radians: float) -> None:
        old: Matrixtuple = self.tuple()
        self._matrix.rotate(radians)
        self.notify(old)

    def scale(self, sx: float, sy: float) -> None:
        old = self.tuple()
        self._matrix.scale(sx, sy)
        self.notify(old)

    def translate(self, tx: float, ty: float) -> None:
        old: Matrixtuple = self.tuple()
        self._matrix.translate(tx, ty)
        self.notify(old)

    def set(
        self,
        xx: float | None = None,
        yx: float | None = None,
        xy: float | None = None,
        yy: float | None = None,
        x0: float | None = None,
        y0: float | None = None,
    ) -> None:
        updated = False
        m = self._matrix
        old = self.tuple()
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
            self.notify(old)

    def multiply(self, m: Matrix) -> Matrix:
        return Matrix(matrix=self._matrix.multiply(m._matrix))

    def transform_distance(
        self, dx: SupportsFloat, dy: SupportsFloat
    ) -> tuple[float, float]:
        return self._matrix.transform_distance(dx, dy)  # type: ignore[no-any-return]

    def transform_point(
        self, x: SupportsFloat, y: SupportsFloat
    ) -> tuple[float, float]:
        return self._matrix.transform_point(x, y)  # type: ignore[no-any-return]

    def inverse(self) -> Matrix:
        m = Matrix(matrix=cairo.Matrix(*self._matrix))
        m.invert()
        return m

    def tuple(self) -> Matrixtuple:
        return tuple(self)  # type: ignore[arg-type, return-value]

    def to_cairo(self) -> cairo.Matrix:
        return self._matrix

    def __eq__(self, other: object) -> bool:
        # sourcery skip: remove-unnecessary-cast
        return (
            bool(self._matrix == other._matrix) if isinstance(other, Matrix) else False
        )

    def __getitem__(self, val: int) -> float:
        return self._matrix[val]  # type: ignore[no-any-return]

    def __mul__(self, other: Matrix) -> Matrix:
        return Matrix(matrix=self._matrix * other._matrix)

    def __imul__(self, other: Matrix) -> Matrix:
        old: Matrixtuple = self.tuple()
        self._matrix *= other._matrix
        self.notify(old)
        return self

    def __repr__(self) -> str:
        return f"Matrix{tuple(self._matrix)}"
