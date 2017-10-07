#!/usr/bin/env python

# Copyright (C) 2008-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Artur Wroblewski <wrobell@pld-linux.org>
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
Generic gaphas item tests.
"""

import unittest

from gaphas.constraint import LineConstraint, \
    EqualsConstraint, LessThanConstraint
from gaphas.item import Item
from gaphas.solver import Variable


class ItemConstraintTestCase(unittest.TestCase):
    """
    Item constraint creation tests. The test check functionality of
    `Item.constraint` method, not constraints themselves.
    """

    def test_line_constraint(self):
        """
        Test line creation constraint.
        """
        item = Item()
        pos = Variable(1), Variable(2)
        line = (Variable(3), Variable(4)), (Variable(5), Variable(6))
        item.constraint(line=(pos, line))
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LineConstraint))
        self.assertEquals((1, 2), c._point)
        self.assertEquals(((3, 4), (5, 6)), c._line)

    def test_horizontal_constraint(self):
        """
        Test horizontal constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(horizontal=(p1, p2))
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on y-axis
        self.assertEquals(2, c.a)
        self.assertEquals(4, c.b)

    def test_vertical_constraint(self):
        """
        Test vertical constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(vertical=(p1, p2))
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on x-axis
        self.assertEquals(1, c.a)
        self.assertEquals(3, c.b)

    def test_left_of_constraint(self):
        """
        Test "less than" constraint (horizontal) creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(left_of=(p1, p2))
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LessThanConstraint))
        self.assertEquals(1, c.smaller)
        self.assertEquals(3, c.bigger)

    def test_above_constraint(self):
        """
        Test "less than" constraint (vertical) creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(above=(p1, p2))
        self.assertEquals(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LessThanConstraint))
        self.assertEquals(2, c.smaller)
        self.assertEquals(4, c.bigger)
