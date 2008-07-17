"""
Some extra picklers needed to gracefully dump and load a canvas.
"""

import copy_reg


# Allow instancemethod to be pickled:

import new

def construct_instancemethod(funcname, self, clazz):
    func = getattr(clazz, funcname)
    return new.instancemethod(func, self, clazz)

def reduce_instancemethod(im):
    return construct_instancemethod, (im.im_func.__name__, im.im_self, im.im_class)

copy_reg.pickle(new.instancemethod, reduce_instancemethod, construct_instancemethod)


# Allow cairo.Matrix to be pickled:

import cairo

def construct_cairo_matrix(*args):
    return cairo.Matrix(*args)

def reduce_cairo_matrix(m):
    return construct_cairo_matrix, tuple(m)

copy_reg.pickle(cairo.Matrix, reduce_cairo_matrix, construct_cairo_matrix)


# vim:sw=4:et:ai
