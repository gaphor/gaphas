# vim:sw=4:et:ai
"""
Geometry functions.

Matrix is imported from cairo.

Rectangle is a utility class for working with rectangles (unions and
intersections)

A point is represented as a tuple (x, y).

"""

# This saves me a lot of coding:
from cairo import Matrix


class Rectangle(object):
    """Python Rectangle implementation. Rectangles can be added (union),
    substituted (intersection) and points and rectangles can be tested to
    be in the rectangle.

    >>> r1= Rectangle(1,1,5,5)
    >>> r2 = Rectangle(3,3,6,7)

    Test if two rectangles intersect:

    >>> if r1 - r2: 'yes'
    'yes'
    """

    def __init__(self, x0=0, y0=0, x1=0, y1=0, width=0, height=0):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1 or x0 + width
        self.y1 = y1 or y0 + height

    def _set_width(self, width):
        self.x1 = self.x0 + width
        
    width = property(lambda s: s.x1 - s.x0, _set_width)

    def _set_heigth(self, height):
        self.y1 = self.y0 + height

    height = property(lambda s: s.y1 - s.y0, _set_heigth)

    def expand(self, delta):
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

    def __add__(self, obj):
        """Create a new Rectangle is the union of the current rectangle
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
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        elif len(obj) == 2:
            # extend using a point
            x0, y0 = obj
            x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." + \
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
        """Create a new Rectangle is the union of the current rectangle
        with another Rectangle or tuple (x0, y0, x1, y1).

        >>> r=Rectangle(5,7,20,25)
        >>> r - (20, 30, 40, 50)
        Rectangle()
        """
        return Rectangle(self.x0, self.y0, self.x1, self.y1).__isub__(obj)

    def __isub__(self, obj):
        """
        >>> r=Rectangle(5,7,20,25)
        >>> r -= (0, 0, 30, 10)
        >>> r
        Rectangle(5, 7, 20, 10)
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." + \
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
        """ Check if a point (x, y), rectangle (x0, y0, x1, y1) or
        Rectangle instance is within the bounds of the rectangle.

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
        """
        if isinstance(obj, Rectangle) or len(obj) == 4:
            x0, y0, x1, y1 = obj
        elif len(obj) == 2:
            # point
            x0, y0 = obj
            x1, y1 = obj
        else:
            raise AttributeError, "Don't know how to handle %s %s." + \
                    " Convert to a Rectangle or tuple first." % (type(obj), obj)
        return x0 >= self.x0 and x1 <= self.x1 and \
               y0 >= self.y0 and y1 <= self.y1


if __name__ == '__main__':
    import doctest
    doctest.testmod()
