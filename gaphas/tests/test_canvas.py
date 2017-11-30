#!/usr/bin/env python

# Copyright (C) 2007-2017 Arjan Molenaar <gaphor@gmail.com>
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

import unittest

import cairo

from gaphas.itemcontainer import ItemContainer, ConnectionError
from gaphas.examples import Box
from gaphas.item import Line


class MatricesTestCase(unittest.TestCase):
    def test_update_matrices(self):
        """Test updating of matrices"""
        c = ItemContainer()
        i = Box()
        ii = Box()
        c.add(i)
        c.add(ii, i)

        i.matrix = (1.0, 0.0, 0.0, 1.0, 5.0, 0.0)
        ii.matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 8.0)

        updated = c.update_matrices([i])

        self.assertEquals(i._matrix_i2c, cairo.Matrix(1, 0, 0, 1, 5, 0))
        self.assertEquals(ii._matrix_i2c, cairo.Matrix(1, 0, 0, 1, 5, 8))

    def test_reparent(self):
        c = ItemContainer()
        b1 = Box()
        b2 = Box()
        c.add(b1)
        c.add(b2, b1)
        c.reparent(b2, None)


# fixme: what about multiple constraints for a handle?
#        what about 1d projection?

def count(i):
    return len(list(i))


class ItemContainerTestCase(unittest.TestCase):
    def test_connect_item(self):
        b1 = Box()
        b2 = Box()
        l = Line()
        c = ItemContainer()
        c.add(b1)
        c.add(b2)
        c.add(l)

        c.connect_item(l, l.handles()[0], b1, b1.ports()[0])
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        # Add the same
        self.assertRaises(ConnectionError, c.connect_item, l, l.handles()[0], b1, b1.ports()[0])
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        # Same item, different port
        # c.connect_item(l, l.handles()[0], b1, b1.ports()[-1])
        # assert count(c.get_connections(handle=l.handles()[0])) == 1

        # Different item
        # c.connect_item(l, l.handles()[0], b2, b2.ports()[0])
        # assert count(c.get_connections(handle=l.handles()[0])) == 1

    def test_disconnect_item_with_callback(self):
        b1 = Box()
        b2 = Box()
        l = Line()
        c = ItemContainer()
        c.add(b1)
        c.add(b2)
        c.add(l)

        events = []

        def callback():
            events.append('called')

        c.connect_item(l, l.handles()[0], b1, b1.ports()[0], callback=callback)
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        c.disconnect_item(l, l.handles()[0])
        assert count(c.get_connections(handle=l.handles()[0])) == 0
        assert events == ['called']

    def test_disconnect_item_with_constraint(self):
        b1 = Box()
        b2 = Box()
        l = Line()
        c = ItemContainer()
        c.add(b1)
        c.add(b2)
        c.add(l)

        cons = b1.ports()[0].constraint(c, l, l.handles()[0], b1)

        c.connect_item(l, l.handles()[0], b1, b1.ports()[0], constraint=cons)
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        ncons = len(c.solver.constraints)
        assert ncons == 5

        c.disconnect_item(l, l.handles()[0])
        assert count(c.get_connections(handle=l.handles()[0])) == 0

        assert len(c.solver.constraints) == 4

    def test_disconnect_item_by_deleting_element(self):
        b1 = Box()
        b2 = Box()
        l = Line()
        c = ItemContainer()
        c.add(b1)
        c.add(b2)
        c.add(l)

        events = []

        def callback():
            events.append('called')

        c.connect_item(l, l.handles()[0], b1, b1.ports()[0], callback=callback)
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        c.remove(b1)

        assert count(c.get_connections(handle=l.handles()[0])) == 0
        assert events == ['called']

    def test_disconnect_item_with_constraint_by_deleting_element(self):
        b1 = Box()
        b2 = Box()
        l = Line()
        c = ItemContainer()
        c.add(b1)
        c.add(b2)
        c.add(l)

        cons = b1.ports()[0].constraint(c, l, l.handles()[0], b1)

        c.connect_item(l, l.handles()[0], b1, b1.ports()[0], constraint=cons)
        assert count(c.get_connections(handle=l.handles()[0])) == 1

        ncons = len(c.solver.constraints)
        assert ncons == 5

        c.remove(b1)

        assert count(c.get_connections(handle=l.handles()[0])) == 0

        self.assertEquals(2, len(c.solver.constraints))


class ConstraintProjectionTestCase(unittest.TestCase):
    def test_line_projection(self):
        """Test projection with line's handle on element's side"""
        line = Line()
        line.matrix.translate(15, 50)
        h1, h2 = line.handles()
        h1.x, h1.y = 0, 0
        h2.x, h2.y = 20, 20

        box = Box()
        box.matrix.translate(10, 10)
        box.width = 40
        box.height = 20
        h_nw, h_ne, h_se, h_sw = box.handles()

        item_container = ItemContainer()
        item_container.add(line)
        item_container.add(box)

        # move line's second handle on box side
        h2.x, h2.y = 5, -20


#        bc = BalanceConstraint(band=(h_sw.x, h_se.x), v=h2.x, balance=0.25)
#        item_container.projector(bc, x={h_sw.x: box, h_se.x: box, h2.x: line})
#        item_container._solver.add_constraint(bc)
#
#        eq = EqualsConstraint(a=h_se.y, b=h2.y)
#        item_container.projector(eq, y={h_se.y: box, h2.y: line})
#        item_container._solver.add_constraint(eq)
#
#        box.request_update()
#        line.request_update()
#
#        item_container.update()
#
#        box.width = 60
#        box.height = 30
#
#        item_container.update()
#
#        # expect h2.x to be moved due to balance constraint
#        self.assertEquals(10, h2.x)
#        self.assertEquals(-10, h2.y)


class CanvasConstraintTestCase(unittest.TestCase):
    def test_remove_connected_item(self):
        """Test adding item_container constraint"""
        item_container = ItemContainer()

        from gaphas.aspect import Connector, ConnectionSink

        l1 = Line()
        item_container.add(l1)

        b1 = Box()
        item_container.add(b1)

        number_cons1 = len(item_container.solver.constraints)

        b2 = Box()
        item_container.add(b2)

        number_cons2 = len(item_container.solver.constraints)

        conn = Connector(l1, l1.handles()[0])
        sink = ConnectionSink(b1, b1.ports()[0])

        conn.connect(sink)

        assert item_container.get_connection(l1.handles()[0])

        conn = Connector(l1, l1.handles()[1])
        sink = ConnectionSink(b2, b2.ports()[0])

        conn.connect(sink)

        assert item_container.get_connection(l1.handles()[1])

        self.assertEquals(number_cons2 + 2, len(item_container.solver.constraints))

        item_container.remove(b1)

        # Expecting a class + line connected at one end only
        self.assertEquals(number_cons1 + 1, len(item_container.solver.constraints))

#    def test_adding_constraint(self):
#        """Test adding item_container constraint"""
#        item_container = ItemContainer()
#
#        l1 = Line()
#        item_container.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        item_container.add_item_container_constraint(l1, h1, eq1)
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertTrue(eq1 in cons[l1][h1])
#
#        l2 = Line()
#        item_container.add(l2)
#
#        h1, h2 = l2.handles()
#        h = Handle()
#
#        eq2 = EqualsConstraint(h1.x, h.x)
#        item_container.add_item_container_constraint(l2, h1, eq2)
#        self.assertTrue(l2 in cons)
#        self.assertTrue(h1 in cons[l2])
#        self.assertTrue(eq2 in cons[l2][h1])
#
#
#    def test_adding_constraint_ex(self):
#        """Test adding item_container constraint for non-existing item"""
#        item_container = ItemContainer()
#        l1 = Line()
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq = EqualsConstraint(h1.x, h.x)
#        self.assertRaises(ValueError, item_container.add_item_container_constraint, l1, h1, eq)
#
#
#    def test_removing_constraint(self):
#        """Test removing item_container constraint"""
#        item_container = ItemContainer()
#        cons = item_container._item_container_constraints
#
#        l1 = Line()
#        item_container.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        item_container.add_item_container_constraint(l1, h1, eq1)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#
#        item_container.remove_item_container_constraint(l1, h1, eq1)
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertFalse(eq1 in cons[l1][h1])
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        eq2 = EqualsConstraint(h1.y, h.y)
#        item_container.add_item_container_constraint(l1, h1, eq1)
#        item_container.add_item_container_constraint(l1, h1, eq2)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#        assert eq2 in cons[l1][h1]
#
#        item_container.remove_item_container_constraint(l1, h1)
#
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertFalse(eq1 in cons[l1][h1])
#        self.assertFalse(eq2 in cons[l1][h1])
#
#
#    def test_fetching_constraints(self):
#        """Test fetching item_container constraints"""
#        item_container = ItemContainer()
#        cons = item_container._item_container_constraints
#
#        l1 = Line()
#        item_container.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        eq2 = EqualsConstraint(h1.y, h.y)
#        item_container.add_item_container_constraint(l1, h1, eq1)
#        item_container.add_item_container_constraint(l1, h1, eq2)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#        assert eq2 in cons[l1][h1]
#
#        self.assertTrue(eq1 in item_container.item_container_constraints(l1))
#        self.assertTrue(eq2 in item_container.item_container_constraints(l1))

# vim:sw=4:et:ai
