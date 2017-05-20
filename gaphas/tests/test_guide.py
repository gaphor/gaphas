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

from __future__ import absolute_import
from __future__ import print_function

import unittest

from gi.repository import Gtk
from six.moves import range

from gaphas.canvas import Canvas
from gaphas.guide import *
from gaphas.item import Element, Line
from gaphas.view import GtkView


class GuideTestCase(unittest.TestCase):
    def setUp(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.window = Gtk.Window()
        self.window.add(self.view)
        self.window.show_all()

    def tearDown(self):
        self.window.destroy()

    def test_find_closest(self):
        """
        test find closest method.
        """
        set1 = [0, 10, 20]
        set2 = [2, 15, 30]

        guider = GuidedItemInMotion(Element(), self.view)
        d, closest = guider.find_closest(set1, set2)
        self.assertEquals(2.0, d)
        self.assertEquals([2.0], closest)

    def test_element_guide(self):
        e1 = Element()
        self.assertEquals(10, e1.width)
        self.assertEquals(10, e1.height)
        guides = Guide(e1).horizontal()
        self.assertEquals(0.0, guides[0])
        self.assertEquals(5.0, guides[1])
        self.assertEquals(10.0, guides[2])
        guides = Guide(e1).vertical()
        self.assertEquals(0.0, guides[0])
        self.assertEquals(5.0, guides[1])
        self.assertEquals(10.0, guides[2])

    def test_line_guide(self):
        c = Canvas()
        l = Line()
        c.add(l)
        l.handles().append(l._create_handle((20, 20)))
        l.handles().append(l._create_handle((30, 30)))
        l.handles().append(l._create_handle((40, 40)))
        l.orthogonal = True
        c.update_now()

        guides = list(Guide(l).horizontal())
        self.assertEquals(2, len(guides))
        self.assertEquals(10.0, guides[0])
        self.assertEquals(40.0, guides[1])

        guides = list(Guide(l).vertical())
        self.assertEquals(2, len(guides))
        self.assertEquals(00.0, guides[0])
        self.assertEquals(20.0, guides[1])

    def test_line_guide_horizontal(self):
        c = Canvas()
        l = Line()
        c.add(l)
        l.handles().append(l._create_handle((20, 20)))
        l.handles().append(l._create_handle((30, 30)))
        l.handles().append(l._create_handle((40, 40)))
        l.horizontal = True
        l.orthogonal = True
        c.update_now()

        guides = list(Guide(l).horizontal())
        self.assertEquals(2, len(guides))
        self.assertEquals(0.0, guides[0])
        self.assertEquals(20.0, guides[1])

        guides = list(Guide(l).horizontal())
        self.assertEquals(2, len(guides))
        self.assertEquals(0.0, guides[0])
        self.assertEquals(20.0, guides[1])

    def test_guide_item_in_motion(self):
        e1 = Element()
        e2 = Element()
        e3 = Element()

        canvas = self.canvas
        canvas.add(e1)
        canvas.add(e2)
        canvas.add(e3)

        self.assertEquals(0, e1.matrix[4])
        self.assertEquals(0, e1.matrix[5])

        e2.matrix.translate(40, 40)
        e2.request_update()
        self.assertEquals(40, e2.matrix[4])
        self.assertEquals(40, e2.matrix[5])

        guider = GuidedItemInMotion(e3, self.view)

        guider.start_move((0, 0))
        self.assertEquals(0, e3.matrix[4])
        self.assertEquals(0, e3.matrix[5])

        # Moved back to guided lines:
        for d in range(0, 3):
            print('move to', d)
            guider.move((d, d))
            self.assertEquals(0, e3.matrix[4])
            self.assertEquals(0, e3.matrix[5])

        for d in range(3, 5):
            print('move to', d)
            guider.move((d, d))
            self.assertEquals(5, e3.matrix[4])
            self.assertEquals(5, e3.matrix[5])

        guider.move((20, 20))
        self.assertEquals(20, e3.matrix[4])
        self.assertEquals(20, e3.matrix[5])

    def test_guide_item_in_motion_2(self):
        e1 = Element()
        e2 = Element()
        e3 = Element()

        canvas = self.canvas
        canvas.add(e1)
        canvas.add(e2)
        canvas.add(e3)

        self.assertEquals(0, e1.matrix[4])
        self.assertEquals(0, e1.matrix[5])

        e2.matrix.translate(40, 40)
        e2.request_update()
        self.assertEquals(40, e2.matrix[4])
        self.assertEquals(40, e2.matrix[5])

        guider = GuidedItemInMotion(e3, self.view)

        guider.start_move((3, 3))
        self.assertEquals(0, e3.matrix[4])
        self.assertEquals(0, e3.matrix[5])

        # Moved back to guided lines:
        for y in range(4, 6):
            print('move to', y)
            guider.move((3, y))
            self.assertEquals(0, e3.matrix[4])
            self.assertEquals(0, e3.matrix[5])

        for y in range(6, 9):
            print('move to', y)
            guider.move((3, y))
            self.assertEquals(0, e3.matrix[4])
            self.assertEquals(5, e3.matrix[5])

        # Take into account initial cursor offset of (3, 3)
        guider.move((20, 23))
        self.assertEquals(17, e3.matrix[4])
        self.assertEquals(20, e3.matrix[5])

# vim:sw=4:et:ai
