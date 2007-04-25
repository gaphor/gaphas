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
    """

    def __init__(self, x0=0, y0=0, x1=0, y1=0, width=0, height=0):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1 or x0 + width
        self.y1 = y1 or y0 + height

    def _set_width(self, width):
        """
        >>> r = Rectangle(-5, 3, 10, 8)
        >>> r.width = 2
        >>> r
        Rectangle(-5, 3, -3, 8)
        """
        self.x1 = self.x0 + width
        
    width = property(lambda s: s.x1 - s.x0, _set_width)

    def _set_heigth(self, height):
        """
        >>> r = Rectangle(-5, 3, 10, 8)
        >>> r.height = 2
        >>> r
        Rectangle(-5, 3, 10, 5)
        """
        self.y1 = self.y0 + height

    height = property(lambda s: s.y1 - s.y0, _set_heigth)

    def expand(self, delta):
        """
        >>> r = Rectangle(-5, 3, 10, 8)
        >>> r.expand(5)
        >>> r
        Rectangle(-10, -2, 15, 13)
        """
        self.x0 -= delta
        self.y0 -= delta
        self.x1 += delta
        self.y1 += delta
        
    def __repr__(self):
        """
        >>> Rectangle(5,7,20,25)
        Rectangle(5, 7, 20, 25)
        """
        if self:
            return '%s(%g, %g, %g, %g)' % (self.__class__.__name__, self.x0, self.y0, self.x1, self.y1)
        return '%s()' % self.__class__.__name__

    def __iter__(self):
        """
        >>> tuple(Rectangle(1,2,3,4))
        (1, 2, 3, 4)
        """
        return iter((self.x0, self.y0, self.x1, self.y1))

    def __getitem__(self, index):
        """
        >>> Rectangle(1,2,3,4)[1]
        2
        """
        return (self.x0, self.y0, self.x1, self.y1)[index]

    def __nonzero__(self):
        """
        >>> r=Rectangle(1,2,3,4)
        >>> if r: 'yes'
        'yes'
        >>> r = Rectangle(1,1,1,1)
        >>> if r: 'no'
        """
        return self.x0 < self.x1 and self.y0 < self.y1
    
    def __eq__(self, other):
        return (type(self) is type(other)) \
                and self.x0 == other.x0 \
                and self.y0 == other.y0 \
                and self.x1 == other.x1 \
                and self.y1 == self.y1

    def __add__(self, obj):
        """
        Create a new Rectangle is the union of the current rectangle
        with another Rectangle, tuple (x,y) or tuple (x0, y0, x1, y1).

        >>> r=Rectangle(5,7,20,25)
        >>> r + (0, 0)
        Rectangle(0, 0, 20, 25)
        >>> r + (20, 30, 40, 50)
        Rectangle(5, 7, 40, 50)
        """
        return Rectangle(self.x0, self.y0, self.x1, self.y1).__iadd__(obj)

    def __iadd__(self, obj):
        """
        >>> r=Rectangle()
        >>> r += Rectangle(5,7,20,25)
        >>> r += (0, 0, 30, 10)
        >>> r
        Rectangle(0, 0, 30, 25)
        >>> r += 'aap'
        Traceback (most recent call last):
          ...
        AttributeError: Don't know how to handle <type 'str'> aap. Convert to a Rectangle first.
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        elif len(obj) == 2:
            # extend using a point
            x0, y0 = obj
            x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." \
                    " Convert to a Rectangle first." % (type(obj), obj)
        if self:
            self.x0 = min(self.x0, x0)
            self.y0 = min(self.y0, y0)
            self.x1 = max(self.x1, x1)
            self.y1 = max(self.y1, y1)
        else:
            self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        return self

    def __sub__(self, obj):
        """
        Create a new Rectangle is the union of the current rectangle
        with another Rectangle or tuple (x0, y0, x1, y1).

        >>> r=Rectangle(5,7,20,25)
        >>> r - (20, 30, 40, 50)
        Rectangle()
        """
        return Rectangle(self.x0, self.y0, self.x1, self.y1).__isub__(obj)

    def __isub__(self, obj):
        """
        >>> r=Rectangle()
        >>> r -= Rectangle(5,7,20,25)
        >>> r -= (0, 0, 30, 10)
        >>> r
        Rectangle(5, 7, 20, 10)
        >>> r -= 'aap'
        Traceback (most recent call last):
          ...
        AttributeError: Don't know how to handle <type 'str'> aap. Convert to a Rectangle first.
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." \
                    " Convert to a Rectangle first." % (type(obj), obj)
        if self:
            self.x0 = max(self.x0, x0)
            self.y0 = max(self.y0, y0)
            self.x1 = min(self.x1, x1)
            self.y1 = min(self.y1, y1)
        else:
            self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

        return self

    def __contains__(self, obj):
        """ Check if a point (x, y) in inside rectangle (x0, y0, x1, y1) or
        if a rectangle instance is inside with the rectangle.

        >>> r=Rectangle(10, 5, width=12, height=12)
        >>> (0, 0) in r
        False
        >>> (10, 6) in r
        True
        >>> (12, 12) in r
        True
        >>> (100, 4) in r
        False
        >>> (11, 6, 15, 15) in r
        True
        >>> Rectangle(11, 6, 15, 15) in r
        True
        >>> 'aap' in r
        Traceback (most recent call last):
          ...
        AttributeError: Don't know how to handle <type 'str'> aap. Convert to a Rectangle or tuple first.
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        elif len(obj) == 2:
            # point
            x0, y0 = obj
            x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." \
                    " Convert to a Rectangle or tuple first." % (type(obj), obj)
        return x0 >= self.x0 and x1 <= self.x1 and \
               y0 >= self.y0 and y1 <= self.y1


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
    Return the distance (fast) from a point to a line.

    >>> distance_rectangle_point(Rectangle(0, 0, 10, 10), (11, -1))
    2
    >>> distance_rectangle_point((0, 0, 10, 10), (11, -1))
    2
    >>> distance_rectangle_point((0, 0, 10, 10), (-1, 11))
    2
    """
    dx = dy = 0

    if point[0] < rect[0]:
        dx = rect[0] - point[0]
    elif point[0] > rect[2]:
        dx = point[0] - rect[2]

    if point[1] < rect[1]:
        dy = rect[1] - point[1]
    elif point[1] > rect[3]:
        dy = point[1] - rect[3]

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
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (4, 7), border=True)
    (4, 10)
    >>> point_on_rectangle((1, 1, 10, 10), (4, 7), border=True)
    (4, 10)
    >>> point_on_rectangle(Rectangle(1, 1, 10, 10), (3, 3), border=True)
    (1, 3)
    """
    px, py = point
    x_inside = y_inside = False

    if px < rect[0]:
        px = rect[0]
    elif px > rect[2]:
        px = rect[2]
    elif border:
        x_inside = True

    if py < rect[1]:
        py = rect[1]
    elif py > rect[3]:
        py = rect[3]
    elif border:
        y_inside = True

    if x_inside and y_inside:
        cx = rect[0] + (rect[2] - rect[0]) / 2
        cy = rect[1] + (rect[3] - rect[1]) / 2
        if abs(cx - px) < abs(cy - py):
            # Handle x axis:
            if py < cy:
                py = rect[1]
            else:
                py = rect[3]
        else:
            if px < cx:
                px = rect[0]
            else:
                px = rect[2]

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
