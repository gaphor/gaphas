import unittest

import cairo

from gaphas.canvas import Canvas, ConnectionError
from gaphas.examples import Box
from gaphas.item import Line


class MatricesTestCase(unittest.TestCase):
    def test_update_matrices(self):
        """Test updating of matrices"""
        c = Canvas()
        i = Box()
        ii = Box()
        c.add(i)
        c.add(ii, i)

        i.matrix = (1.0, 0.0, 0.0, 1.0, 5.0, 0.0)
        ii.matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 8.0)

        updated = c.update_matrices([i])

        self.assertEqual(i._matrix_i2c, cairo.Matrix(1, 0, 0, 1, 5, 0))
        self.assertEqual(ii._matrix_i2c, cairo.Matrix(1, 0, 0, 1, 5, 8))

    def test_reparent(self):
        c = Canvas()
        b1 = Box()
        b2 = Box()
        c.add(b1)
        c.add(b2, b1)
        c.reparent(b2, None)


# fixme: what about multiple constraints for a handle?
#        what about 1d projection?


def count(i):
    return len(list(i))


class CanvasTestCase(unittest.TestCase):
    def test_connect_item(self):
        b1 = Box()
        b2 = Box()
        line = Line()
        c = Canvas()
        c.add(b1)
        c.add(b2)
        c.add(line)

        c.connect_item(line, line.handles()[0], b1, b1.ports()[0])
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        # Add the same
        self.assertRaises(
            ConnectionError, c.connect_item, line, line.handles()[0], b1, b1.ports()[0]
        )
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        # Same item, different port
        # c.connect_item(l, l.handles()[0], b1, b1.ports()[-1])
        # assert count(c.get_connections(handle=l.handles()[0])) == 1

        # Different item
        # c.connect_item(l, l.handles()[0], b2, b2.ports()[0])
        # assert count(c.get_connections(handle=l.handles()[0])) == 1

    def test_disconnect_item_with_callback(self):
        b1 = Box()
        b2 = Box()
        line = Line()
        c = Canvas()
        c.add(b1)
        c.add(b2)
        c.add(line)

        events = []

        def callback():
            events.append("called")

        c.connect_item(line, line.handles()[0], b1, b1.ports()[0], callback=callback)
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        c.disconnect_item(line, line.handles()[0])
        assert count(c.get_connections(handle=line.handles()[0])) == 0
        assert events == ["called"]

    def test_disconnect_item_with_constraint(self):
        b1 = Box()
        b2 = Box()
        line = Line()
        c = Canvas()
        c.add(b1)
        c.add(b2)
        c.add(line)

        cons = b1.ports()[0].constraint(c, line, line.handles()[0], b1)

        c.connect_item(line, line.handles()[0], b1, b1.ports()[0], constraint=cons)
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        ncons = len(c.solver.constraints)
        assert ncons == 5

        c.disconnect_item(line, line.handles()[0])
        assert count(c.get_connections(handle=line.handles()[0])) == 0

        assert len(c.solver.constraints) == 4

    def test_disconnect_item_by_deleting_element(self):
        b1 = Box()
        b2 = Box()
        line = Line()
        c = Canvas()
        c.add(b1)
        c.add(b2)
        c.add(line)

        events = []

        def callback():
            events.append("called")

        c.connect_item(line, line.handles()[0], b1, b1.ports()[0], callback=callback)
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        c.remove(b1)

        assert count(c.get_connections(handle=line.handles()[0])) == 0
        assert events == ["called"]

    def test_disconnect_item_with_constraint_by_deleting_element(self):
        b1 = Box()
        b2 = Box()
        line = Line()
        c = Canvas()
        c.add(b1)
        c.add(b2)
        c.add(line)

        cons = b1.ports()[0].constraint(c, line, line.handles()[0], b1)

        c.connect_item(line, line.handles()[0], b1, b1.ports()[0], constraint=cons)
        assert count(c.get_connections(handle=line.handles()[0])) == 1

        ncons = len(c.solver.constraints)
        assert ncons == 5

        c.remove(b1)

        assert count(c.get_connections(handle=line.handles()[0])) == 0

        self.assertEqual(2, len(c.solver.constraints))


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

        canvas = Canvas()
        canvas.add(line)
        canvas.add(box)

        # move line's second handle on box side
        h2.x, h2.y = 5, -20


#        bc = BalanceConstraint(band=(h_sw.x, h_se.x), v=h2.x, balance=0.25)
#        canvas.projector(bc, x={h_sw.x: box, h_se.x: box, h2.x: line})
#        canvas._solver.add_constraint(bc)
#
#        eq = EqualsConstraint(a=h_se.y, b=h2.y)
#        canvas.projector(eq, y={h_se.y: box, h2.y: line})
#        canvas._solver.add_constraint(eq)
#
#        box.request_update()
#        line.request_update()
#
#        canvas.update()
#
#        box.width = 60
#        box.height = 30
#
#        canvas.update()
#
#        # expect h2.x to be moved due to balance constraint
#        self.assertEqual(10, h2.x)
#        self.assertEqual(-10, h2.y)


class CanvasConstraintTestCase(unittest.TestCase):
    def test_remove_connected_item(self):
        """Test adding canvas constraint"""
        canvas = Canvas()

        from gaphas.aspect import Connector, ConnectionSink

        l1 = Line()
        canvas.add(l1)

        b1 = Box()
        canvas.add(b1)

        number_cons1 = len(canvas.solver.constraints)

        b2 = Box()
        canvas.add(b2)

        number_cons2 = len(canvas.solver.constraints)

        conn = Connector(l1, l1.handles()[0])
        sink = ConnectionSink(b1, b1.ports()[0])

        conn.connect(sink)

        assert canvas.get_connection(l1.handles()[0])

        conn = Connector(l1, l1.handles()[1])
        sink = ConnectionSink(b2, b2.ports()[0])

        conn.connect(sink)

        assert canvas.get_connection(l1.handles()[1])

        self.assertEqual(number_cons2 + 2, len(canvas.solver.constraints))

        canvas.remove(b1)

        # Expecting a class + line connected at one end only
        self.assertEqual(number_cons1 + 1, len(canvas.solver.constraints))


#    def test_adding_constraint(self):
#        """Test adding canvas constraint"""
#        canvas = Canvas()
#
#        l1 = Line()
#        canvas.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        canvas.add_canvas_constraint(l1, h1, eq1)
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertTrue(eq1 in cons[l1][h1])
#
#        l2 = Line()
#        canvas.add(l2)
#
#        h1, h2 = l2.handles()
#        h = Handle()
#
#        eq2 = EqualsConstraint(h1.x, h.x)
#        canvas.add_canvas_constraint(l2, h1, eq2)
#        self.assertTrue(l2 in cons)
#        self.assertTrue(h1 in cons[l2])
#        self.assertTrue(eq2 in cons[l2][h1])
#
#
#    def test_adding_constraint_ex(self):
#        """Test adding canvas constraint for non-existing item"""
#        canvas = Canvas()
#        l1 = Line()
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq = EqualsConstraint(h1.x, h.x)
#        self.assertRaises(ValueError, canvas.add_canvas_constraint, l1, h1, eq)
#
#
#    def test_removing_constraint(self):
#        """Test removing canvas constraint"""
#        canvas = Canvas()
#        cons = canvas._canvas_constraints
#
#        l1 = Line()
#        canvas.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        canvas.add_canvas_constraint(l1, h1, eq1)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#
#        canvas.remove_canvas_constraint(l1, h1, eq1)
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertFalse(eq1 in cons[l1][h1])
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        eq2 = EqualsConstraint(h1.y, h.y)
#        canvas.add_canvas_constraint(l1, h1, eq1)
#        canvas.add_canvas_constraint(l1, h1, eq2)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#        assert eq2 in cons[l1][h1]
#
#        canvas.remove_canvas_constraint(l1, h1)
#
#        self.assertTrue(l1 in cons)
#        self.assertTrue(h1 in cons[l1])
#        self.assertFalse(eq1 in cons[l1][h1])
#        self.assertFalse(eq2 in cons[l1][h1])
#
#
#    def test_fetching_constraints(self):
#        """Test fetching canvas constraints"""
#        canvas = Canvas()
#        cons = canvas._canvas_constraints
#
#        l1 = Line()
#        canvas.add(l1)
#
#        h1, h2 = l1.handles()
#        h = Handle()
#
#        eq1 = EqualsConstraint(h1.x, h.x)
#        eq2 = EqualsConstraint(h1.y, h.y)
#        canvas.add_canvas_constraint(l1, h1, eq1)
#        canvas.add_canvas_constraint(l1, h1, eq2)
#
#        # test preconditions
#        assert l1 in cons
#        assert h1 in cons[l1]
#        assert eq1 in cons[l1][h1]
#        assert eq2 in cons[l1][h1]
#
#        self.assertTrue(eq1 in canvas.canvas_constraints(l1))
#        self.assertTrue(eq2 in canvas.canvas_constraints(l1))

# vim:sw=4:et:ai
