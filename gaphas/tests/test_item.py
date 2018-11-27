"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.constraint import LineConstraint, EqualsConstraint, LessThanConstraint
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
        self.assertEqual(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LineConstraint))
        self.assertEqual((1, 2), c._point)
        self.assertEqual(((3, 4), (5, 6)), c._line)

    def test_horizontal_constraint(self):
        """
        Test horizontal constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(horizontal=(p1, p2))
        self.assertEqual(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on y-axis
        self.assertEqual(2, c.a)
        self.assertEqual(4, c.b)

    def test_vertical_constraint(self):
        """
        Test vertical constraint creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(vertical=(p1, p2))
        self.assertEqual(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, EqualsConstraint))
        # expect constraint on x-axis
        self.assertEqual(1, c.a)
        self.assertEqual(3, c.b)

    def test_left_of_constraint(self):
        """
        Test "less than" constraint (horizontal) creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(left_of=(p1, p2))
        self.assertEqual(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LessThanConstraint))
        self.assertEqual(1, c.smaller)
        self.assertEqual(3, c.bigger)

    def test_above_constraint(self):
        """
        Test "less than" constraint (vertical) creation.
        """
        item = Item()
        p1 = Variable(1), Variable(2)
        p2 = Variable(3), Variable(4)
        item.constraint(above=(p1, p2))
        self.assertEqual(1, len(item._constraints))

        c = item._constraints[0]
        self.assertTrue(isinstance(c, LessThanConstraint))
        self.assertEqual(2, c.smaller)
        self.assertEqual(4, c.bigger)
