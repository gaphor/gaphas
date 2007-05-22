import gaphas
from gaphas.solver import Solver, Variable
from gaphas.constraint import EqualsConstraint, LessThanConstraint

def speed_setup():
    """
    Speed test setup. Example of test run::

        python -m timeit.py -s 'from gaphas.tests.test_solver import speed_setup, speed_run_weakest; speed_setup()' 'speed_run_weakest()'
    """
    global solver, v1, v2, v3, c_eq
    solver = gaphas.solver.Solver()

    v1, v2, v3 = Variable(1.0), Variable(2.0), Variable(3.0)
    c_eq = EqualsConstraint(v1, v2)
    solver.add_constraint(c_eq)

def speed_run_weakest():
    """
    Speed test for weakest variable.peed_run_weakest()'

    """
    global solver, v1, v2, v3, c_eq

    v1.value = 5.0
    solver.weakest_variable(c_eq.variables())
