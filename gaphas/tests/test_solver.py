"""
Unit tests for Gaphas' solver.
"""

import unittest
from timeit import Timer

from gaphas.solver import Solver, Variable
from gaphas.constraint import EquationConstraint


SETUP = """
from gaphas.solver import Solver, Variable
from gaphas.constraint import EqualsConstraint, LessThanConstraint
solver = Solver()
v1, v2, v3 = Variable(1.0), Variable(2.0), Variable(3.0)
c_eq = EqualsConstraint(v1, v2)
solver.add_constraint(c_eq)
"""

# Timeit constants
REPEAT = 30
NUMBER = 1000

class WeakestVariableTestCase(unittest.TestCase):
    """
    Test weakest variable calculation.
    """
    def test_weakest_list(self):
        """Test weakest list"""
        solver = Solver()
        a = Variable(1, 30)
        b = Variable(2, 10)
        c = Variable(3, 10)

        c_eq = EquationConstraint(lambda a, b, c: a + b + c, a=a, b=b, c=c)

        # because of kwargs above we cannot test by the order of arguments
        self.assertTrue(b in c_eq._weakest)
        self.assertTrue(c in c_eq._weakest)


    def test_weakest_list_order(self):
        """Test weakest list order"""
        solver = Solver()
        a = Variable(1, 30)
        b = Variable(2, 10)
        c = Variable(3, 10)

        c_eq = EquationConstraint(lambda a, b, c: a + b + c, a=a, b=b, c=c)

        weakest = [el for el in c_eq._weakest]
        a.value = 4

        self.assertEqual(c_eq._weakest, weakest) # does not change if non-weak variable changed

        b.value = 5
        self.assertEqual(c_eq.weakest(), c)

        b.value = 6
        self.assertEqual(c_eq.weakest(), c)

        # b changed above, now change a - all weakest variables changed
        # return the oldest changed variable then
        c.value = 6
        self.assertEqual(c_eq.weakest(), b)

        b.value = 6
        self.assertEqual(c_eq.weakest(), c)


    def test_strength_change(self):
        """Test strength change"""
        solver = Solver()
        a = Variable(1, 30)
        b = Variable(2, 10)
        c = Variable(3, 10)

        c_eq = EquationConstraint(lambda a, b, c: a + b + c, a=a, b=b, c=c)

        b.strength = 9
        self.assertEqual(c_eq._weakest, [b])


class SolverSpeedTestCase(unittest.TestCase):
    """
    Solver speed tests.
    """
    def test_speed_run_weakest(self):
        """
        Speed test for weakest variable.
        """

        results = Timer(setup=SETUP, stmt="""
v1.value = 5.0
c_eq.weakest()""").repeat(repeat=REPEAT, number=NUMBER)

        # Print the average of the best 10 runs:
        results.sort()
        print '[Avg: %gms]' % ((sum(results[:10]) / 10) * 1000)


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
