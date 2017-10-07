#!/usr/bin/env python

# Copyright (C) 2009-2017 Arjan Molenaar <gaphor@gmail.com>
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

from gaphas.connector import Position, Handle
from gaphas.solver import Variable


class PositionTestCase(unittest.TestCase):
    def test_position(self):
        pos = Position((0, 0))
        self.assertEquals(0, pos.x)
        self.assertEquals(0, pos.y)

    def test_position(self):
        pos = Position((1, 2))
        self.assertEquals(1, pos.x)
        self.assertEquals(2, pos.y)

    def test_set_xy(self):
        pos = Position((1, 2))
        x = Variable()
        y = Variable()
        assert x is not pos.x
        assert y is not pos.y

        pos.set_x(x)
        pos.set_y(y)
        assert x is pos.x
        assert y is pos.y


class HandleTestCase(unittest.TestCase):
    def test_handle_x_y(self):
        h = Handle()
        self.assertEquals(0.0, h.x)
        self.assertEquals(0.0, h.y)

# vim: sw=4:et:ai
