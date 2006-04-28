"""
This module contains several flavors of constraint solver classes.
Each has a method solve_for(name) and a method set(**kwds). These methods
are used by the constraint solver (solver.Solver) to set the variables.

Variables should be of type solver.Variable.

Available constraints are:
 - EqualsConstraint - make 'a' and 'b' equal
 - LessThanConstraint - ensure one variable stays smaller than the orther
 - EquationConstraint - solve a linear equation

# TODO:
 - LineConstraint - Solves the equation where a line is connected to
       a line or side at a specific point.
 - LineToCenterConstraint - constraint to be used when a line connects
       to a rectangular element. The line is connected on the side, but
       keeps opointing to the center
 - ShortestLineConstraint - The last segment of the line is pointing to
       a rectangualar or line like object and the length of the line
       is kept to a minimum
"""

__version__ = "$Revision$"
# $HeadURL$

from __future__ import division

class Constraint(object):
    """Constraint base class.
    """

    def set(self, **kwargs):
        raise NotImplemented

    def solve_for(self, name):
        raise NotImplemented


class EqualsConstraint(Constraint):
    """Simple Constraint, takes two arguments: 'a' and 'b'. When solved the
    attribute passed to solve_for() is set equal to the other.

    >>> from solver import Variable
    >>> a, b = Variable(1.0), Variable(2.0)
    >>> eq = EqualsConstraint(a, b)
    >>> eq.solve_for('a')
    >>> a
    Variable(2, 20)
    >>> a.value = 10.8
    >>> eq.solve_for('b')
    >>> b
    Variable(10.8, 20)
    """

    def __init__(self, a=None, b=None):
        self.a = a
        self.b = b

    def set(self, a, b):
        self.a = a
        self.b = b

    def solve_for(self, name):
        assert name in ('a', 'b')

        if name == 'a':
            self.a.value = self.b.value
        else:
            self.b.value = self.a.value


class LessThanConstraint(Constraint):
    """Ensure @smaller is less than @bigger. The variable that is passed
    as to-be-solved is left alone (cause it is the variable that has not
    been moved lately). Instead the other variable is solved.

    >>> from solver import Variable
    >>> a, b = Variable(3.0), Variable(2.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b)
    >>> lt.solve_for('smaller')
    >>> a, b
    (Variable(3, 20), Variable(3, 20))
    >>> b.value = 0.8
    >>> lt.solve_for('bigger')
    >>> a, b
    (Variable(0.8, 20), Variable(0.8, 20))
    """

    def __init__(self, smaller=None, bigger=None):
        self.smaller = smaller
        self.bigger = bigger

    def set(self, smaller, bigger):
        self.smaller = smaller
        self.bigger = bigger

    def solve_for(self, name):
        if self.smaller.value > self.bigger.value:
            if name == 'smaller':
                self.bigger.value = self.smaller.value
            elif name == 'bigger':
                self.smaller.value = self.bigger.value


# Constants for the EquationConstraint
TOL = 0.0000001      # tolerance
ITERLIMIT = 1000        # iteration limit

class EquationConstraint(Constraint):
    """Equation solver using attributes and introspection.

    Takes a function, named arg value (opt.) and returns a Constraint object
    Calling EquationConstraint.solve_for will solve the equation for
    variable @arg, so that the outcome is 0.

    >>> from solver import Variable
    >>> a, b, c = Variable(), Variable(4), Variable(5)
    >>> cons = EquationConstraint(lambda a, b, c: a + b - c, a=a, b=b, c=c)
    >>> cons.solve_for('a')
    >>> a
    Variable(1, 20)
    >>> a.value = 3.4
    >>> cons.solve_for('b')
    >>> b
    Variable(1.6, 20)

    From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/303396
    """
    
    def __init__(self, f, **args):
        self._f = f
        self._args = {}
        # see important note on order of operations in __setattr__ below.
        for arg in f.func_code.co_varnames[0:f.func_code.co_argcount]:
            self._args[arg] = None
        self.set(**args)

    def __repr__(self):
        argstring = ', '.join(['%s=%s' % (arg, str(value)) for (arg, value) in
                             self._args.items()])
        if argstring:
            return 'Constraint(%s, %s)' % (self._f.func_code.co_name, argstring)
        else:
            return 'Constraint(%s)' % self._f.func_code.co_name

    def __getattr__(self, name):
        """used to extract function argument values
        """
        self._args[name]
        return self.solve_for(name)

    def __setattr__(self, name, value):
        """sets function argument values"""
        # Note - once self._args is created, no new attributes can
        # be added to self.__dict__.  This is a good thing as it throws
        # an exception if you try to assign to an arg which is inappropriate
        # for the function in the solver.
        if self.__dict__.has_key('_args'):
            if name in self._args:
                self._args[name] = value
            else:
                raise KeyError, name
        else:
            object.__setattr__(self, name, value)

    def set(self, **args):
        """sets values of function arguments
        """
        for arg in args:
            self._args[arg]  # raise exception if arg not in _args
            setattr(self, arg, args[arg])

    def solve_for(self, arg):
        """Solve this constraint for the variable named 'arg' in the
        constraint.
        """
        var = self._args[arg]
        args = {}
        for nm, v in self._args.items():
            args[nm] = v.value
        var.value = self._solve_for(arg, args)

    def _solve_for(self, arg, args):
        """Newton's method solver"""
        #args = self._args
        close_runs = 10   # after getting close, do more passes
        if args[arg]:
            x0 = args[arg]
        else:
            x0 = 1
        if x0 == 0:
            x1 = 1
        else:
            x1 = x0*1.1
        def f(x):
            """function to solve"""
            args[arg] = x
            return self._f(**args)
        fx0 = f(x0)
        n = 0
        while 1:                    # Newton's method loop here
            fx1 = f(x1)
            if fx1 == 0 or x1 == x0:  # managed to nail it exactly
                break
            if abs(fx1-fx0) < TOL:    # very close
                close_flag = True
                if close_runs == 0:       # been close several times
                    break
                else:
                    close_runs -= 1       # try some more
            else:
                close_flag = False
            if n > ITERLIMIT:
                print "Failed to converge; exceeded iteration limit"
                break
            slope = (fx1 - fx0) / (x1 - x0)
            if slope == 0:
                if close_flag:  # we're close but have zero slope, finish
                    break
                else:
                    print 'Zero slope and not close enough to solution'
                    break
            x2 = x0 - fx0 / slope           # New 'x1'
            fx0 = fx1
            x0 = x1
            x1 = x2
            n += 1
        #args[arg] = x1
        return x1


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
