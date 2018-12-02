"""
Some Gaphor specific updates to the canvas. This is done by setting
the correct properties on gaphas' modules.

Matrix
------
Small utility class wrapping cairo.Matrix. The `Matrix` class adds
state preservation capabilities.
"""
from __future__ import absolute_import
from __future__ import division

from builtins import object

__version__ = "$Revision$"
# $HeadURL$

import cairo
from .state import observed, reversible_method


class Matrix(object):
    """
    Matrix wrapper. This version sends @observed messages on state changes

    >>> cairo.Matrix()
    cairo.Matrix(1, 0, 0, 1, 0, 0)
    >>> Matrix()
    Matrix(1, 0, 0, 1, 0, 0)
    """

    def __init__(self, xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0):
        self._matrix = cairo.Matrix(xx, yx, xy, yy, x0, y0)

    @staticmethod
    def init_rotate(radians):
        return cairo.Matrix.init_rotate(radians)

    @observed
    def invert(self):
        return self._matrix.invert()

    @observed
    def rotate(self, radians):
        return self._matrix.rotate(radians)

    @observed
    def scale(self, sx, sy):
        return self._matrix.scale(sx, sy)

    @observed
    def translate(self, tx, ty):
        self._matrix.translate(tx, ty)

    @observed
    def multiply(self, m):
        return self._matrix.multiply(m)

    reversible_method(invert, invert)
    reversible_method(rotate, rotate, {"radians": lambda radians: -radians})
    reversible_method(scale, scale, {"sx": lambda sx: 1 / sx, "sy": lambda sy: 1 / sy})
    reversible_method(
        translate, translate, {"tx": lambda tx: -tx, "ty": lambda ty: -ty}
    )

    def transform_distance(self, dx, dy):
        self._matrix.transform_distance(dx, dy)

    def transform_point(self, x, y):
        self._matrix.transform_point(x, y)

    def __eq__(self, other):
        return self._matrix.__eq__(other)

    def __ne__(self, other):
        return self._matrix.__ne__(other)

    def __le__(self, other):
        return self._matrix.__le__(other)

    def __lt__(self, other):
        return self._matrix.__lt__(other)

    def __ge__(self, other):
        return self._matrix.__ge__(other)

    def __gt__(self, other):
        return self._matrix.__gt__(other)

    def __getitem__(self, val):
        return self._matrix.__getitem__(val)

    @observed
    def __mul__(self, other):
        return self._matrix.__mul__(other)

    @observed
    def __rmul__(self, other):
        return self._matrix.__rmul__(other)

    def __repr__(self):
        return "Matrix(%g, %g, %g, %g, %g, %g)" % tuple(self._matrix)


# vim:sw=4:et
