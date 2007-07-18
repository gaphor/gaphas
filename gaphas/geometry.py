"""
Geometry functions.

Rectangle is a utility class for working with rectangles (unions and
intersections)

A point is represented as a tuple (x, y).

"""

__version__ = "$Revision$"
# $HeadURL$

from math import sqrt


class Rectangle(object):
    """
    Python Rectangle implementation. Rectangles can be added (union),
    substituted (intersection) and points and rectangles can be tested to
    be in the rectangle.

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

    def __init__(self, x=0, y=0, width=None, height=None, x1=0, y1=0):
        self.x = x
        self.y = y
        if width is None:
            self.width = x1 - x
        else:
            self.width = width
        if height is None:
            self.height = y1 - y
        else:
            self.height = height

    def _set_x1(self, x1):
        """
        """
        width = x1 - self.x
        if width < 0: width = 0
        self.width = width
        
    x1 = property(lambda s: s.x + s.width, _set_x1)

    def _set_y1(self, y1):
        """
        """
        height = y1 - self.y
        if height < 0: height = 0
        self.height = height

    y1 = property(lambda s: s.y + s.height, _set_y1)

    def expand(self, delta):
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
        
    def __repr__(self):
        """
        >>> Rectangle(5,7,20,25)
        Rectangle(5, 7, 20, 25)
        """
        if self:
            return '%s(%g, %g, %g, %g)' % (self.__class__.__name__, self.x, self.y, self.width, self.height)
        return '%s()' % self.__class__.__name__

    def __iter__(self):
        """
        >>> tuple(Rectangle(1,2,3,4))
        (1, 2, 3, 4)
        """
        return iter((self.x, self.y, self.width, self.height))

    def __getitem__(self, index):
        """
        >>> Rectangle(1,2,3,4)[1]
        2
        """
        return (self.x, self.y, self.width, self.height)[index]

    def __nonzero__(self):
        """
        >>> r=Rectangle(1,2,3,4)
        >>> if r: 'yes'
        'yes'
        >>> r = Rectangle(1,1,0,0)
        >>> if r: 'no'
        """
        return self.width > 0 and self.height > 0
    
    def __eq__(self, other):
        return (type(self) is type(other)) \
                and self.x == other.x \
                and self.y == other.y \
                and self.width == other.width \
                and self.height == self.height

    def __add__(self, obj):
        """
        Create a new Rectangle is the union of the current rectangle
        with another Rectangle, tuple (x,y) or tuple (x, y, width, height).

        >>> r=Rectangle(5, 7, 20, 25)
        >>> r + (0, 0)
        Traceback (most recent call last):
          ...
        AttributeError: Can only add Rectangle or tuple (x, y, width, height), not (0, 0).
        >>> r + (20, 30, 40, 50)
        Rectangle(5, 7, 55, 73)
        """
        return Rectangle(self.x, self.y, self.width, self.height).__iadd__(obj)

    def __iadd__(self, obj):
        """
        >>> r = Rectangle()
        >>> r += Rectangle(5, 7, 20, 25)
        >>> r += (0, 0, 30, 10)
        >>> r
        Rectangle(0, 0, 30, 32)
        >>> r += 'aap'
        Traceback (most recent call last):
          ...
        AttributeError: Can only add Rectangle or tuple (x, y, width, height), not 'aap'.
        """
        try:
            x, y, width, height = obj
        except ValueError:
            raise AttributeError, "Can only add Rectangle or tuple (x, y, width, height), not %s." % repr(obj)
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

    def __sub__(self, obj):
        """
        Create a new Rectangle is the union of the current rectangle
        with another Rectangle or tuple (x, y, width, height).

        >>> r = Rectangle(5, 7, 20, 25)
        >>> r - (20, 30, 40, 50)
        Rectangle(20, 30, 5, 2)
        >>> r - (30, 40, 40, 50)
        Rectangle()
        """
        return Rectangle(self.x, self.y, self.width, self.height).__isub__(obj)

    def __isub__(self, obj):
        """
        >>> r = Rectangle()
        >>> r -= Rectangle(5, 7, 20, 25)
        >>> r -= (0, 0, 30, 10)
        >>> r
        Rectangle(5, 7, 20, 3)
        >>> r -= 'aap'
        Traceback (most recent call last):
          ...
        AttributeError: Can only substract Rectangle or tuple (x, y, width, height), not 'aap'.
        """
        try:
            x, y, width, height = obj
        except ValueError:
            raise AttributeError, "Can only substract Rectangle or tuple (x, y, width, height), not %s." % repr(obj)
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

    def __contains__(self, obj):
        """
        Check if a point (x, y) in inside rectangle (x, y, width, height)
        or if a rectangle instance is inside with the rectangle.

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
        AttributeError: Should compare to Rectangle, tuple (x, y, width, height) or point (x, y), not 'aap'.
        """
        try:
            x, y, width, height = obj
            x1, y1 = x + width, y + width
        except ValueError:
            # point
            try:
                x, y = obj
                x1, y1 = obj
            except ValueError:
                raise AttributeError, "Should compare to Rectangle, tuple (x, y, width, height) or point (x, y), not %s." % repr(obj)
        return x >= self.x and x1 <= self.x1 and \
               y >= self.y and y1 <= self.y1


def distance_point_point(point1, point2=(0., 0.)):
    """
    >>> '%.3f' % distance_point_point((0,0), (1,1))
    '1.414'
    """
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return sqrt(dx*dx + dy*dy)


def distance_point_point_fast(point1, point2):
    """
    >>> distance_point_point_fast((0,0), (1,1))
    2
    """
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return abs(dx) + abs(dy)


def distance_rectangle_point(rect, point):
    """
    Return the distance (fast) from a rectangle (x, y, width, height) to a line.

    >>> distance_rectangle_point(Rectangle(0, 0, 10, 10), (11, -1))
    2
    >>> distance_rectangle_point((0, 0, 10, 10), (11, -1))
    2
    >>> distance_rectangle_point((0, 0, 10, 10), (-1, 11))
    2
    """
    dx = dy = 0
    px, py = point
    rx, ry, rw, rh = tuple(rect)

    if px < rx:
        dx = rx - px
    elif px > rx + rw:
        dx = px - (rx + rw)

    if py < ry:
        dy = ry - py
    elif py > ry + rh:
        dy = py - (ry + rh)

    return abs(dx) + abs(dy)


def point_on_rectangle(rect, point, border=False):
    """
    Return the point on which @point can be projecten on the rectangle.
    border = True will make sure the point is bound to the border of
    the reactangle. Otherwise, if the point is in the rectangle, it's okay.
    
    >>> point_on_rectangle(Rectangle(0, 0, 10, 10), (11, -1))
    (10, 0)
    >>> point_on_rectangle((0, 0, 10, 10), (5, 12))
    (5, 10)
    >>> point_on_rectangle(Rectangle(0, 0, 10, 10), (12, 5))
    (10, 5)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (3, 4))
    (3, 4)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (0, 3))
    (1, 3)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (4, 3))
    (4, 3)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (4, 9), border=True)
    (4, 11)
    >>> point_on_rectangle((1, 1, 10, 10), (4, 6), border=True)
    (1, 6)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (3, 3), border=True)
    (1, 3)
    >>> point_on_rectangle((1, 1, 10, 100), (5, 8), border=True)
    (1, 8)
    >>> point_on_rectangle((1, 1, 10, 100), (5, 98), border=True)
    (5, 101)
    """
    px, py = point
    rx, ry, rw, rh = tuple(rect)
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
        # Find point on side closest to the point
        if min(abs(rx - px), abs(rx + rw - px)) > \
           min(abs(ry - py), abs(ry + rh - py)):
            if py < ry + rh / 2.:
                py = ry
            else:
                py = ry + rh
        else:
            if px < rx + rw / 2.:
                px = rx
            else:
                px = rx + rw

    return px, py


def distance_line_point(line_start, line_end, point):
    """
    Calculate the distance of a point from a line. The line is marked
    by begin and end point line_start and line_end. 

    A tuple is returned containing the distance and point on the line.

    >>> distance_line_point((0., 0.), (2., 4.), point=(3., 4.))
    (1.0, (2.0, 4.0))
    >>> distance_line_point((0., 0.), (2., 4.), point=(-1., 0.))
    (1.0, (0.0, 0.0))
    >>> distance_line_point((0., 0.), (2., 4.), point=(1., 2.))
    (0.0, (1.0, 2.0))
    >>> d, p = distance_line_point((0., 0.), (2., 4.), point=(2., 2.))
    >>> '%.3f' % d
    '0.894'
    >>> '(%.3f, %.3f)' % p
    '(1.200, 2.400)'
    """
    # The original end point:
    true_line_end = line_end

    # "Move" the line, so it "starts" on (0, 0)
    line_end = line_end[0] - line_start[0], line_end[1] - line_start[1]
    point = point[0] - line_start[0], point[1] - line_start[1]

    line_len_sqr = line_end[0] * line_end[0] + line_end[1] * line_end[1]

    # Both points are very near each other.
    if line_len_sqr < 0.0001:
        return distance_point_point(point), line_start

    projlen = (line_end[0] * point[0] + line_end[1] * point[1]) / line_len_sqr

    if projlen < 0.0:
        # Closest point is the start of the line.
        return distance_point_point(point), line_start
    elif projlen > 1.0:
        # Point has a projection after the line_end.
        return distance_point_point(point, line_end), true_line_end
    else:
        # Projection is on the line. multiply the line_end with the projlen
        # factor to obtain the point on the line.
        proj = line_end[0] * projlen, line_end[1] * projlen
        return distance_point_point((proj[0] - point[0], proj[1] - point[1])),\
               (line_start[0] + proj[0], line_start[1] + proj[1])


def intersect_line_line(line1_start, line1_end, line2_start, line2_end):
    """
    >>> intersect_line_line((0, 0), (10, 10), (3, 0), (8, 10))
    (6.0, 6.0)
    >>> intersect_line_line((0, 0), (0, 10), (3, 0), (8, 10))
    >>> intersect_line_line((0, 0), (0, 10), (3, 0), (3, 10))
    """
    x1, y1 = line1_start
    x2, y2 = line1_end
    u1, v1 = line2_start
    u2, v2 = line2_end

    try:
        b1 = (y2 - y1) / float(x2 - x1)
    except ZeroDivisionError:
        # line 1 is vertical, we'll approach that with a very big number
        b1 = 1E199

    try:    
        b2 = (v2 - v1) / float(u2 - u1)
    except ZeroDivisionError:
        # line 2 is vertical
        b2 = 1E199
        
    a1 = y1 - b1 * x1
    a2 = v1 - b2 * u1

    try:    
        xi = - (a1 - a2) / (b1 - b2)
    except ZeroDivisionError:
        # two lines are parallel
        return None
    
    yi = a1 + b1 * xi
    if (x1 - xi) * (xi - x2) >= 0 and (u1 - xi) * (xi - u2) >= 0 \
       and (y1 - yi) * (yi - y2) >= 0 and (v1 - yi) * (yi - v2) >= 0:
        return xi, yi


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
