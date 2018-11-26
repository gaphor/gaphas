import unittest

from gaphas.solver import Variable
from gaphas.constraint import PositionConstraint, LineAlignConstraint


class PositionTestCase(unittest.TestCase):
    def test_pos_constraint(self):
        """Test position constraint"""
        x1, y1 = Variable(10), Variable(11)
        x2, y2 = Variable(12), Variable(13)
        pc = PositionConstraint(origin=(x1, y1), point=(x2, y2))
        pc.solve_for()

        # origin shall remain the same
        self.assertEqual(10, x1)
        self.assertEqual(11, y1)

        # point shall be moved to origin
        self.assertEqual(10, x2)
        self.assertEqual(11, y2)

        # change just x of origin
        x1.value = 15
        pc.solve_for()
        self.assertEqual(15, x2)

        # change just y of origin
        y1.value = 14
        pc.solve_for()
        self.assertEqual(14, y2)


class LineAlignConstraintTestCase(unittest.TestCase):
    """
    Line align constraint test case.
    """

    def test_delta(self):
        """Test line align delta
        """
        line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        point = (Variable(15), Variable(10))
        lc = LineAlignConstraint(line=line, point=point, align=0.5, delta=5)
        lc.solve_for()
        self.assertAlmostEqual(19.16, point[0].value, 2)
        self.assertAlmostEqual(12.77, point[1].value, 2)

        line[1][0].value = 40
        line[1][1].value = 30
        lc.solve_for()
        self.assertAlmostEqual(24.00, point[0].value, 2)
        self.assertAlmostEqual(18.00, point[1].value, 2)

    def test_delta_below_zero(self):
        """Test line align with delta below zero
        """
        line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        point = (Variable(15), Variable(10))
        lc = LineAlignConstraint(line=line, point=point, align=0.5, delta=-5)
        lc.solve_for()
        self.assertAlmostEqual(10.84, point[0].value, 2)
        self.assertAlmostEqual(7.23, point[1].value, 2)

        line[1][0].value = 40
        line[1][1].value = 30
        lc.solve_for()
        self.assertAlmostEqual(16.0, point[0].value, 2)
        self.assertAlmostEqual(12.00, point[1].value, 2)


# vim: sw=4:et:ai
