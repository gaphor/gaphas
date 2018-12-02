"""
Unit tests for Gaphas' solver.
"""
from __future__ import print_function
from __future__ import division

import unittest
from timeit import Timer

from gaphas.solver import Solver, Variable
from gaphas.constraint import EquationConstraint, EqualsConstraint, LessThanConstraint


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
        solver.add_constraint(c_eq)

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
        solver.add_constraint(c_eq)

        weakest = [el for el in c_eq._weakest]
        a.value = 4

        self.assertEqual(
            c_eq._weakest, weakest
        )  # does not change if non-weak variable changed

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
        solver.add_constraint(c_eq)

        b.strength = 9
        self.assertEqual(c_eq._weakest, [b])


class SizeTestCase(unittest.TestCase):
    """
    Test size related constraints, i.e. minimal size.
    """

    def test_min_size(self):
        """Test minimal size constraint"""
        solver = Solver()
        v1 = Variable(0)
        v2 = Variable(10)
        v3 = Variable(10)
        c1 = EqualsConstraint(a=v2, b=v3)
        c2 = LessThanConstraint(smaller=v1, bigger=v3, delta=10)
        solver.add_constraint(c1)
        solver.add_constraint(c2)

        # check everyting is ok on start
        solver.solve()
        self.assertEqual(0, v1)
        self.assertEqual(10, v2)
        self.assertEqual(10, v3)

        # change v1 to 2, after solve it should be 0 again due to LT
        # constraint
        v1.value = 2
        solver.solve()

        self.assertEqual(0, v1)
        self.assertEqual(10, v2)
        self.assertEqual(10, v3)

        # change v3 to 20, after solve v2 will follow thanks to EQ
        # constraint
        v3.value = 20
        solver.solve()

        self.assertEqual(0, v1)
        self.assertEqual(20, v2)
        self.assertEqual(20, v3)

        # change v3 to 0, after solve it shoul be 10 due to LT.delta = 10,
        # v2 should also be 10 due to EQ constraint
        v3.value = 0
        solver.solve()

        self.assertEqual(0, v1)
        self.assertEqual(10, v2)
        self.assertEqual(10, v3)


class SolverSpeedTestCase(unittest.TestCase):
    """
    Solver speed tests.
    """

    def _test_speed_run_weakest(self):
        """
        Speed test for weakest variable.
        """

        results = Timer(
            setup=SETUP,
            stmt="""
v1.value = 5.0
c_eq.weakest()""",
        ).repeat(repeat=REPEAT, number=NUMBER)

        # Print the average of the best 10 runs:
        results.sort()
        print("[Avg: %gms]" % ((sum(results[:10]) / 10)) * 1000)


if __name__ == "__main__":
    unittest.main()

# vim:sw=4:et:ai
