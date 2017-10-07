#!/usr/bin/env python

# Copyright (C) 2008-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.

"""
Some extra picklers needed to gracefully dump and load a canvas.
"""

import types
import cairocffi as cairo
import copyreg


def construct_instancemethod(funcname, self, clazz):
    func = getattr(clazz, funcname)
    return types.MethodType(func, self, clazz)


def reduce_instancemethod(im):
    return construct_instancemethod, (im.__func__.__name__, im.__self__, im.__self__.__class__)


copyreg.pickle(types.MethodType, reduce_instancemethod, construct_instancemethod)

# Allow cairo.Matrix to be pickled:


def construct_cairo_matrix(*args):
    return cairo.Matrix(*args)


def reduce_cairo_matrix(m):
    return construct_cairo_matrix, tuple(m)


copyreg.pickle(cairo.Matrix, reduce_cairo_matrix, construct_cairo_matrix)


# vim:sw=4:et:ai
