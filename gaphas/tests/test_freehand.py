#!/usr/bin/env python

# Copyright (C) 2010-2017 Arjan Molenaar <gaphor@gmail.com>
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

import unittest

import cairo

from gaphas.freehand import FreeHandCairoContext


class PseudoFile(object):
    def __init__(self):
        self.data = ''

    def write(self, data):
        print(data)
        self.data = self.data + data


class FreeHandCairoContextTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_drawing_lines(self):
        f = PseudoFile()

        surface = cairo.SVGSurface('freehand-drawing-lines.svg', 100, 100)
        cr = FreeHandCairoContext(cairo.Context(surface))
        cr.set_line_width(2)
        cr.move_to(20, 20)
        cr.line_to(20, 80)
        cr.line_to(80, 80)
        cr.line_to(80, 20)
        cr.stroke()
        cr.show_page()

    def test_drawing_rectangle(self):
        surface = cairo.SVGSurface('freehand-drawing-rectangle.svg', 100, 100)
        cr = FreeHandCairoContext(cairo.Context(surface))
        cr.set_line_width(2)
        cr.rectangle(20, 20, 60, 60)
        cr.stroke()
        cr.show_page()


DRAWING_LINES_OUTPUT = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100pt" height="100pt"viewBox="0 0 100 100" version="1.1">
<g id="surface0">
<path style="fill:none;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke:rgb(0%,0%,0%);stroke-opacity:1;stroke-miterlimit:10;" d="M 20 20 C 23.324219 50.054688 17.195312 33.457031 20.722656 80.585938 C 38.78125 83.566406 20.984375 77.625 80.652344 80.652344 C 83.65625 70.992188 77.578125 60.988281 80.507812 20.019531 "/>
</g>
</svg>"""

# vim:sw=4:et:ai
