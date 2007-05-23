"""
Unit tests for Gaphas' solver, mainly for speed testing.
"""

import unittest
from timeit import Timer


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

class SolverSpeedTestCase(unittest.TestCase):

    def test_speed_run_weakest(self):
        """
        Speed test for weakest variable.
        """

        results = Timer(setup=SETUP, stmt="""
v1.value = 5.0
solver.weakest_variable(c_eq.variables())""").repeat(repeat=REPEAT, number=NUMBER)

        # Print the average of the best 10 runs:
        results.sort()
        print '[Avg: %gms]' % ((sum(results[:10]) / 10) * 1000)


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
