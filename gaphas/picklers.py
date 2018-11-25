"""
Some extra picklers needed to gracefully dump and load a canvas.
"""

from future import standard_library

standard_library.install_aliases()
import copyreg


# Allow instancemethod to be pickled:
import types


def construct_instancemethod(funcname, self, clazz):
    func = getattr(clazz, funcname)
    return types.MethodType(func, self, clazz)


def reduce_instancemethod(im):
    return (
        construct_instancemethod,
        (im.__func__.__name__, im.__self__, im.__self__.__class__),
    )


copyreg.pickle(types.MethodType, reduce_instancemethod, construct_instancemethod)


# Allow cairo.Matrix to be pickled:

import cairo


def construct_cairo_matrix(*args):
    return cairo.Matrix(*args)


def reduce_cairo_matrix(m):
    return construct_cairo_matrix, tuple(m)


copyreg.pickle(cairo.Matrix, reduce_cairo_matrix, construct_cairo_matrix)


# vim:sw=4:et:ai
