"""Test constraint solver.

"""
from timeit import Timer

import pytest

from gaphas.constraint import EqualsConstraint, EquationConstraint, LessThanConstraint
from gaphas.solver import Solver, Variable

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


class SolverFixture:
    def __init__(self):
        self.solver = Solver()
        self.a = Variable(1, 30)
        self.b = Variable(2, 10)
        self.c = Variable(3, 10)
        self.c_eq = EquationConstraint(
            lambda a, b, c: a + b + c, a=self.a, b=self.b, c=self.c
        )
        self.solver.add_constraint(self.c_eq)


@pytest.fixture(name="solv")
def solver_fixture():
    return SolverFixture()


def test_weakest_list(solv):
    """Test weakest list.

    """
    assert solv.b in solv.c_eq._weakest
    assert solv.c in solv.c_eq._weakest


def test_weakest_list_order(solv):
    """Test weakest list order.

    """
    weakest = [el for el in solv.c_eq._weakest]
    solv.a.value = 4

    assert solv.c_eq._weakest == weakest  # Does not change if non-weak variable changed

    solv.b.value = 5
    assert solv.c_eq.weakest() == solv.c

    solv.b.value = 6
    assert solv.c_eq.weakest() == solv.c

    # b changed above, now change a - all weakest variables changed return the
    # oldest changed variable
    solv.c.value = 6
    assert solv.c_eq.weakest() == solv.b

    solv.b.value = 6
    assert solv.c_eq.weakest() == solv.c


def test_strength_change(solv):
    """Test strength change.

    """
    solv.b.strength = 9
    assert solv.c_eq._weakest == [solv.b]


def test_min_size(solv):
    """Test minimal size constraint.

    """
    v1 = Variable(0)
    v2 = Variable(10)
    v3 = Variable(10)
    c1 = EqualsConstraint(a=v2, b=v3)
    c2 = LessThanConstraint(smaller=v1, bigger=v3, delta=10)
    solv.solver.add_constraint(c1)
    solv.solver.add_constraint(c2)

    # Check everything is ok on start
    solv.solver.solve()
    assert 0 == v1
    assert 10 == v2
    assert 10 == v3

    # Change v1 to 2, after solve it should be 0 again due to LT constraint
    v1.value = 2
    solv.solver.solve()

    assert 0 == v1
    assert 10 == v2
    assert 10 == v3

    # Change v3 to 20, after solve v2 will follow thanks to EQ constraint
    v3.value = 20
    solv.solver.solve()

    assert 0 == v1
    assert 20 == v2
    assert 20 == v3

    # Change v3 to 0, after solve it should be 10 due to LT.delta = 10, v2
    # should also be 10 due to EQ constraint
    v3.value = 0
    solv.solver.solve()

    assert 0 == v1
    assert 10 == v2
    assert 10 == v3


def test_speed_run_weakest():
    """Speed test for weakest variable.

    """
    results = Timer(
        setup=SETUP,
        stmt="""
v1.value = 5.0
c_eq.weakest()""",
    ).repeat(repeat=REPEAT, number=NUMBER)

    # Print the average of the best 10 runs:
    results.sort()
    print(f"[Avg: {(sum(results[:10]) / 10) * 1000}ms]")
