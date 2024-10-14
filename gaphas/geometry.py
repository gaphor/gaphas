"""Geometry functions.

Rectangle is a utility class for working with rectangles (unions and
intersections).

A point is represented as a tuple `(x, y)`.
"""

from __future__ import annotations

from math import sqrt
from collections.abc import Iterator

Point = tuple[float, float]  # x, y
Rect = tuple[float, float, float, float]  # x, y, width, height


class Rectangle:
    """Python Rectangle implementation. Rectangles can be added (union),
    substituted (intersection) and points and rectangles can be tested to be in
    the rectangle.

    >>> r1= Rectangle(1,1,5,5)
    >>> r2 = Rectangle(3,3,6,7)

    Test if two rectangles intersect:

    >>> if r1 - r2: 'yes'
    'yes'

    >>> r1, r2 = Rectangle(1,2,3,4), Rectangle(1,2,3,4)
    >>> r1 == r2
    True

    >>> r = Rectangle(-5, 3, 10, 8)
    >>> r.width = 2
    >>> r
    Rectangle(-5, 3, 2, 8)

    >>> r = Rectangle(-5, 3, 10, 8)
    >>> r.height = 2
    >>> r
    Rectangle(-5, 3, 10, 2)
    """

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: float | None = None,
        height: float | None = None,
        x1: float = 0,
        y1: float = 0,
    ):
        if width is None:
            self.x = min(x, x1)
            self.width = abs(x1 - x)
        else:
            self.x = x
            self.width = width
        if height is None:
            self.y = min(y, y1)
            self.height = abs(y1 - y)
        else:
            self.y = y
            self.height = height

    @property
    def x1(self) -> float:
        return self.x + self.width

    @x1.setter
    def x1(self, x1: float) -> None:
        width = x1 - self.x
        width = max(width, 0)
        self.width = width

    @property
    def y1(self) -> float:
        return self.y + self.height

    @y1.setter
    def y1(self, y1: float) -> None:
        height = y1 - self.y
        height = max(height, 0)
        self.height = height

    def expand(self, delta: float) -> None:
        """
        >>> r = Rectangle(-5, 3, 10, 8)
        >>> r.expand(5)
        >>> r
        Rectangle(-10, -2, 20, 18)
        """
        self.x -= delta
        self.y -= delta
        self.width += delta * 2
        self.height += delta * 2

    def tuple(self) -> tuple[float, float, float, float]:
        """A type safe version of `tuple(rectangle)`."""
        return (self.x, self.y, self.width, self.height)

    def __repr__(self) -> str:
        """
        >>> Rectangle(5,7,20,25)
        Rectangle(5, 7, 20, 25)
        """
        if self:
            return f"{self.__class__.__name__}({self.x}, {self.y}, {self.width}, {self.height})"
        return f"{self.__class__.__name__}()"

    def __iter__(self) -> Iterator[float]:
        """
        >>> tuple(Rectangle(1,2,3,4))
        (1, 2, 3, 4)
        """
        return iter((self.x, self.y, self.width, self.height))

    def __getitem__(self, index: int) -> float:
        """
        >>> Rectangle(1,2,3,4)[1]
        2
        """
        return (self.x, self.y, self.width, self.height)[index]

    def __bool__(self) -> bool:
        """
        >>> r=Rectangle(1,2,3,4)
        >>> if r: 'yes'
        'yes'
        >>> r = Rectangle(1,1,0,0)
        >>> if r: 'no'
        """
        return self.width > 0 and self.height > 0

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Rectangle)
            and self.x == other.x
            and self.y == other.y
            and self.width == other.width
            and self.height == other.height
        )

    def __add__(self, obj: Rectangle | Rect) -> Rectangle:
        """Create a new Rectangle is the union of the current rectangle with
        another Rectangle, tuple `(x,y)` or tuple `(x, y, width, height)`.

        >>> r=Rectangle(5, 7, 20, 25)
        >>> r + (0, 0)
        Traceback (most recent call last):
          ...
        TypeError: Can only add Rectangle or tuple (x, y, width, height), not (0, 0).
        >>> r + (20, 30, 40, 50)
        Rectangle(5, 7, 55, 73)
        """
        return Rectangle(self.x, self.y, self.width, self.height).__iadd__(obj)

    def __iadd__(self, obj: Rectangle | Rect) -> Rectangle:
        """
        >>> r = Rectangle()
        >>> r += Rectangle(5, 7, 20, 25)
        >>> r += (0, 0, 30, 10)
        >>> r
        Rectangle(0, 0, 30, 32)
        >>> r += 'aap'
        Traceback (most recent call last):
          ...
        TypeError: Can only add Rectangle or tuple (x, y, width, height), not 'aap'.
        """
        try:
            x, y, width, height = obj
        except ValueError as e:
            raise TypeError(
                f"Can only add Rectangle or tuple (x, y, width, height), not {obj!r}."
            ) from e

        x1, y1 = x + width, y + height
        if self:
            ox1, oy1 = self.x + self.width, self.y + self.height
            self.x = min(self.x, x)
            self.y = min(self.y, y)
            self.x1 = max(ox1, x1)
            self.y1 = max(oy1, y1)
        else:
            self.x, self.y, self.width, self.height = x, y, width, height
        return self

    def __sub__(self, obj: Rectangle | Rect) -> Rectangle:
        """Create a new Rectangle is the union of the current rectangle with
        another Rectangle or tuple (x, y, width, height).

        >>> r = Rectangle(5, 7, 20, 25)
        >>> r - (20, 30, 40, 50)
        Rectangle(20, 30, 5, 2)
        >>> r - (30, 40, 40, 50)
        Rectangle()
        """
        return Rectangle(self.x, self.y, self.width, self.height).__isub__(obj)

    def __isub__(self, obj: Rectangle | Rect) -> Rectangle:
        """
        >>> r = Rectangle()
        >>> r -= Rectangle(5, 7, 20, 25)
        >>> r -= (0, 0, 30, 10)
        >>> r
        Rectangle(5, 7, 20, 3)
        >>> r -= 'aap'
        Traceback (most recent call last):
          ...
        TypeError: Can only subtract Rectangle or tuple (x, y, width, height), not 'aap'.
        """
        try:
            x, y, width, height = obj
        except ValueError as e:
            raise TypeError(
                f"Can only subtract Rectangle or tuple (x, y, width, height), not {obj!r}."
            ) from e

        x1, y1 = x + width, y + height

        if self:
            ox1, oy1 = self.x + self.width, self.y + self.height
            self.x = max(self.x, x)
            self.y = max(self.y, y)
            self.x1 = min(ox1, x1)
            self.y1 = min(oy1, y1)
        else:
            self.x, self.y, self.width, self.height = x, y, width, height

        return self

    def __contains__(self, obj: Rectangle | Rect | Point) -> bool:
        """Check if a point `(x, y)` in inside rectangle `(x, y, width,
        height)` or if a rectangle instance is inside with the rectangle.

        >>> r=Rectangle(10, 5, 12, 12)
        >>> (0, 0) in r
        False
        >>> (10, 6) in r
        True
        >>> (12, 12) in r
        True
        >>> (100, 4) in r
        False
        >>> (11, 6, 5, 5) in r
        True
        >>> (11, 6, 15, 15) in r
        False
        >>> Rectangle(11, 6, 5, 5) in r
        True
        >>> Rectangle(11, 6, 15, 15) in r
        False
        >>> 'aap' in r
        Traceback (most recent call last):
          ...
        TypeError: Should compare to Rectangle, tuple (x, y, width, height) or point (x, y), not 'aap'.
        """
        try:
            x, y, width, height = obj  # type: ignore[misc]
            x1, y1 = x + width, y + width
        except ValueError:
            # point
            try:
                (x, y) = (x1, y1) = obj  # type: ignore[misc]
            except ValueError as e:
                raise TypeError(
                    f"Should compare to Rectangle, tuple (x, y, width, height) or point (x, y), not {obj!r}."
                ) from e

        return x >= self.x and x1 <= self.x1 and y >= self.y and y1 <= self.y1


def distance_point_point(point1: Point, point2: Point = (0.0, 0.0)) -> float:
    """Return the distance from point ``point1`` to ``point2``.

    >>> f"{distance_point_point((0,0), (1,1)):.3f}"
    '1.414'
    """
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return sqrt(dx * dx + dy * dy)


def distance_point_point_fast(point1: Point, point2: Point = (0.0, 0.0)) -> float:
    """Return the distance from point ``point1`` to ``point2``. This version is
    faster than ``distance_point_point()``, but less precise.

    >>> distance_point_point_fast((0,0), (1,1))
    2
    """
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return abs(dx) + abs(dy)


def distance_rectangle_border_point(rect: Rect | Rectangle, point: Point) -> float:
    """Return the distance (fast) from a rectangle ``(x, y, width,height)`` to
    a ``point``."""
    dx = dy = 0.0
    px, py = point
    rx, ry, rw, rh = rect  # typing: ignore[misc]
    rx1 = rx + rw
    ry1 = ry + rh

    if rx < px < rx1 and ry < py < ry1:
        return -min(px - rx, rx1 - px, py - ry, ry1 - py)

    if px < rx:
        dx = rx - px
    elif px > rx1:
        dx = px - rx1

    if py < ry:
        dy = ry - py
    elif py > ry1:
        dy = py - ry1

    return abs(dx) + abs(dy)


def distance_rectangle_point(rect: Rect | Rectangle, point: Point) -> float:
    """Return the distance (fast) from a rectangle ``(x, y, width,height)`` to
    a ``point``."""
    return max(0, distance_rectangle_border_point(rect, point))


def point_on_rectangle(
    rect: Rect | Rectangle, point: Point, border: bool = False
) -> Point:
    """Return the point on which ``point`` can be projecten on the rectangle.

    ``border = True`` will make sure the point is bound to
    the border of the reactangle. Otherwise, if the point is in the
    rectangle, it's okay.
    """
    px, py = point
    rx, ry, rw, rh = rect
    x_inside = y_inside = False

    if px < rx:
        px = rx
    elif px > rx + rw:
        px = rx + rw
    elif border:
        x_inside = True

    if py < ry:
        py = ry
    elif py > ry + rh:
        py = ry + rh
    elif border:
        y_inside = True

    if x_inside and y_inside:
        if min(abs(rx - px), abs(rx + rw - px)) > min(abs(ry - py), abs(ry + rh - py)):
            py = ry if py < ry + rh / 2.0 else ry + rh
        else:
            px = rx if px < rx + rw / 2.0 else rx + rw
    return px, py


def distance_line_point(
    line_start: Point, line_end: Point, point: Point
) -> tuple[float, Point]:
    """Calculate the distance of a ``point`` from a line. The line is marked by
    begin and end point ``line_start`` and ``line_end``.

    A tuple is returned containing the distance and point on the line.
    """
    # The original end point:
    true_line_end = line_end

    # "Move" the line, so it "starts" on (0, 0)
    line_end = line_end[0] - line_start[0], line_end[1] - line_start[1]
    point = point[0] - line_start[0], point[1] - line_start[1]

    line_len_sqr = line_end[0] * line_end[0] + line_end[1] * line_end[1]

    # Both points are very near each other.
    if line_len_sqr < 0.0001:
        return distance_point_point(point), (line_start[0], line_start[1])

    projlen = (line_end[0] * point[0] + line_end[1] * point[1]) / line_len_sqr

    if projlen < 0.0:
        # Closest point is the start of the line.
        return distance_point_point(point), (line_start[0], line_start[1])
    elif projlen > 1.0:
        # Point has a projection after the line_end.
        return distance_point_point(point, line_end), (
            true_line_end[0],
            true_line_end[1],
        )
    else:
        # Projection is on the line. multiply the line_end with the projlen
        # factor to obtain the point on the line.
        proj = line_end[0] * projlen, line_end[1] * projlen
        return (
            distance_point_point((proj[0] - point[0], proj[1] - point[1])),
            (line_start[0] + proj[0], line_start[1] + proj[1]),
        )


def intersect_line_line(
    line1_start: Point, line1_end: Point, line2_start: Point, line2_end: Point
) -> Point | None:
    """Find the point where the lines (segments) defined by ``(line1_start,
    line1_end)`` and ``(line2_start, line2_end)`` intersect.  If no
    intersection occurs, ``None`` is returned.

    >>> intersect_line_line((3, 0), (8, 10), (0, 0), (10, 10))
    (6, 6)
    >>> intersect_line_line((0, 0), (10, 10), (3, 0), (8, 10))
    (6, 6)
    >>> intersect_line_line((0, 0), (10, 10), (8, 10), (3, 0))
    (6, 6)
    >>> intersect_line_line((8, 10), (3, 0), (0, 0), (10, 10))
    (6, 6)
    >>> intersect_line_line((0, 0), (0, 10), (3, 0), (8, 10))
    >>> intersect_line_line((0, 0), (0, 10), (3, 0), (3, 10))

    Ticket #168:
    >>> intersect_line_line((478.0, 117.0), (478.0, 166.0), (527.5, 141.5), (336.5, 139.5))
    (478.5, 141.48167539267016)
    >>> intersect_line_line((527.5, 141.5), (336.5, 139.5), (478.0, 117.0), (478.0, 166.0))
    (478.5, 141.48167539267016)

    This is a Python translation of the ``lines_intersect``, C Code from
    Graphics Gems II, Academic Press, Inc. The original routine was written
    by Mukesh Prasad.

    EULA: The Graphics Gems code is copyright-protected. In other words, you
    cannot claim the text of the code as your own and resell it. Using the code
    is permitted in any program, product, or library, non-commercial or
    commercial. Giving credit is not required, though is a nice gesture. The
    code comes as-is, and if there are any flaws or problems with any Gems
    code, nobody involved with Gems - authors, editors, publishers, or
    webmasters - are to be held responsible. Basically, don't be a jerk, and
    remember that anything free comes with no guarantee.
    """
    #
    #   This function computes whether two line segments,
    #   respectively joining the input points (x1,y1) -- (x2,y2)
    #   and the input points (x3,y3) -- (x4,y4) intersect.
    #   If the lines intersect, the output variables x, y are
    #   set to coordinates of the point of intersection.
    #
    #   All values are in integers.  The returned value is rounded
    #   to the nearest integer point.
    #
    #   If non-integral grid points are relevant, the function
    #   can easily be transformed by substituting floating point
    #   calculations instead of integer calculations.
    #
    #   Entry
    #        x1, y1,  x2, y2   Coordinates of endpoints of one segment.
    #        x3, y3,  x4, y4   Coordinates of endpoints of other segment.
    #
    #   Exit
    #        x, y              Coordinates of intersection point.
    #
    #   The value returned by the function is one of:
    #
    #        DONT_INTERSECT    0
    #        DO_INTERSECT      1
    #        COLLINEAR         2
    #
    # Error conditions:
    #
    #     Depending upon the possible ranges, and particularly on 16-bit
    #     computers, care should be taken to protect from overflow.
    #
    #     In the following code, 'long' values have been used for this
    #     purpose, instead of 'int'.
    #

    x1, y1 = line1_start
    x2, y2 = line1_end
    x3, y3 = line2_start
    x4, y4 = line2_end

    # long a1, a2, b1, b2, c1, c2; /* Coefficients of line eqns. */
    # long r1, r2, r3, r4;         /* 'Sign' values */
    # long denom, offset, num;     /* Intermediate values */

    # Compute a1, b1, c1, where line joining points 1 and 2
    # is "a1 x  +  b1 y  +  c1  =  0".

    a1 = y2 - y1
    b1 = x1 - x2
    c1 = x2 * y1 - x1 * y2

    # Compute r3 and r4.

    r3 = a1 * x3 + b1 * y3 + c1
    r4 = a1 * x4 + b1 * y4 + c1

    # Check signs of r3 and r4.  If both point 3 and point 4 lie on
    # same side of line 1, the line segments do not intersect.

    if r3 and r4 and (r3 * r4) >= 0:
        return None  # ( DONT_INTERSECT )

    # Compute a2, b2, c2

    a2 = y4 - y3
    b2 = x3 - x4
    c2 = x4 * y3 - x3 * y4

    # Compute r1 and r2

    r1 = a2 * x1 + b2 * y1 + c2
    r2 = a2 * x2 + b2 * y2 + c2

    # Check signs of r1 and r2.  If both point 1 and point 2 lie
    # on same side of second line segment, the line segments do
    # not intersect.

    if r1 and r2 and (r1 * r2) >= 0:  # SAME_SIGNS( r1, r2 ))
        return None  # ( DONT_INTERSECT )

    # Line segments intersect: compute intersection point.
    # The denom / 2 is to get rounding instead of truncating.  It
    # is added or subtracted to the numerator, depending upon the
    # sign of the numerator.

    denom = a1 * b2 - a2 * b1
    x_num = b1 * c2 - b2 * c1
    y_num = a2 * c1 - a1 * c2
    if not denom:
        return None  # ( COLLINEAR )

    offset = abs(denom) / 2
    x = ((x_num - offset) if (x_num < 0) else (x_num + offset)) / denom
    y = ((y_num - offset) if (y_num < 0) else (y_num + offset)) / denom
    return x, y


def rectangle_contains(inner: Rect, outer: Rect) -> bool:
    """Returns True if ``inner`` rect is contained in ``outer`` rect."""
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih


def rectangle_intersects(recta: Rect, rectb: Rect) -> bool:
    """Return True if ``recta`` and ``rectb`` intersect.

    >>> rectangle_intersects((5,5,20, 20), (10, 10, 1, 1))
    True
    >>> rectangle_intersects((40, 30, 10, 1), (1, 1, 1, 1))
    False
    """
    ax, ay, aw, ah = recta
    bx, by, bw, bh = rectb
    return ax <= bx + bw and ax + aw >= bx and ay <= by + bh and ay + ah >= by


def rectangle_clip(recta: Rect, rectb: Rect) -> Rect | None:
    """Return the clipped rectangle of ``recta`` and ``rectb``. If they do not
    intersect, ``None`` is returned.

    >>> rectangle_clip((0, 0, 20, 20), (10, 10, 20, 20))
    (10, 10, 10, 10)
    """
    ax, ay, aw, ah = recta
    bx, by, bw, bh = rectb
    x = max(ax, bx)
    y = max(ay, by)
    w = min(ax + aw, bx + bw) - x
    h = min(ay + ah, by + bh) - y
    return None if w < 0 or h < 0 else (x, y, w, h)
