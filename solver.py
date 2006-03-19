
from operator import isCallable
from constraint import Constraint

# Variable Strengths:
VERY_WEAK = 0
WEAK = 10
NORMAL = 20
STRONG = 30
VERY_STRONG = 40
REQUIRED = 100

class Variable(object):
    """Representation of a variable in the constraint solver.
    Each Variable has a @value and a @strength. Ina constraint the
    weakest variables are changed.
    """

    def __init__(self, value=0.0, strength=NORMAL):
        self._value = value
        self._strength = strength

        # These variables are set by the Solver:
        self._solver = None
        self._constraints = set()

    strength = property(lambda s: s._strength)

    def set_value(self, value):
        self._value = value
        if self._solver:
            self._solver.mark_dirty(self)

    value = property(lambda s: s._value, set_value)

    def __str__(self):
        return 'Variable(%f, %d)' % (self._value, self._strength)
    __repr__ = __str__


class Solver(object):
    """Solve constraints. A constraint should have accompanying
    variables.
    """

    def __init__(self):
        # a dict of constraint -> name/variable mappings
        self._constraints = {}
        self._marked_vars = []
        self._marked_cons = []

    def mark_dirty(self, variable):
        """Mark a variable as "dirty". This means it it solved the next time
        the constraints are resolved.

        Example:
        >>> a,b,c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s=Solver()
        >>> s.add_constraint(lambda a,b: a+b, a=a, b=b)
        Constraint(<lambda>,a=None,b=None)
        >>> s._marked_vars
        []
        >>> s._marked_cons
        [Constraint(<lambda>,a=None,b=None)]
        >>> a.value=5.0
        >>> s._marked_vars
        [Variable(5.000000, 20)]
        >>> b.value=2.0
        >>> s._marked_vars
        [Variable(5.000000, 20), Variable(2.000000, 20)]
        >>> a.value=5.0
        >>> s._marked_vars
        [Variable(2.000000, 20), Variable(5.000000, 20)]
        """
        if variable in self._marked_vars:
            self._marked_vars.remove(variable)
        self._marked_vars.append(variable)
        for c in variable._constraints:
            if c in self._marked_cons:
                self._marked_cons.remove(c)
            self._marked_cons.append(c)

    def add_constraint(self, constraint, **variables):
        """Add a constraint.
        The actual constraint is returned, so the constraint can be removed
        later on.

        Example:
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(lambda a, b: a -b, a=a, b=b)
        Constraint(<lambda>,a=None,b=None)
        >>> a.value
        0.0
        >>> b.value
        2.0
        >>> len(s._constraints)
        1
        """
        if isCallable(constraint):
            constraint = Constraint(constraint)
        self._constraints[constraint] = dict(variables)
        self._marked_cons.append(constraint)
        for v in variables.values():
            v._constraints.add(constraint)
            v._solver = self
        return constraint

    def remove_constraint(self, constraint):
        """ Remove a constraint from the solver
        """
        for v in self._constraints[constraint]: v._constraints.remove(constraint)
        del self._constraints[constraint]
        if self._marked_cons.get(constraint):
            del self._marked_cons[constraint]

    def weakest_variable(self, variables):
        """Returns the name(!) of the weakest variable.

	Example:
	>>> s = Solver()
	>>> s.weakest_variable({'a': Variable(2.0, 30), 'b': Variable(2.0, 20)})
	('b', Variable(2.000000, 20))
        >>> a,b,c = Variable(), Variable(), Variable()
        >>> s._marked_vars = [a, b, c]
        """
        marked_vars = self._marked_vars
        wname, wvar = None, None
        for n, v in variables.items():
            if not wvar or \
                (v.strength < wvar.strength) or \
                (v.strength == wvar.strength and \
                 (v not in marked_vars
                  or wvar in marked_vars and \
                  marked_vars.index(v) < marked_vars.index(wvar))):
                wname, wvar = n, v
        return wname, wvar

    def solve(self):
        """
        Example:
        >>> a,b,c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s=Solver()
        >>> s.add_constraint(lambda a,b: a+b, a=a, b=b)
        Constraint(<lambda>,a=None,b=None)
        >>> a.value=5.0
        >>> s.solve()
        >>> len(s._marked_cons)
        0
        >>> b._value
        -5.0
        >>> s.add_constraint(lambda a,b: a+b, a=b, b=c)
        Constraint(<lambda>,a=None,b=None)
        >>> len(s._constraints)
        2
        >>> len(s._marked_cons)
        1
        >>> s.solve()
        >>> b._value
        -5.0
        """
        constraints = self._constraints
        marked_cons = self._marked_cons

        # Solve each constraint. Using a counter makes it
        # possible to also solve constraints that are marked as
        # a result of other variabled being solved.
        n = 0
        while n < len(marked_cons):
            c = marked_cons[n]
            wname, wvar = self.weakest_variable(constraints[c])
            xx = {}
            for nm, v in constraints[c].items():
              xx[nm] = v.value
            c.set(**xx)
            wvar.value = c.solve_for(wname)
            n += 1

        self._marked_cons = []
        self._marked_vars = []

if __name__ == '__main__':
    import doctest
    doctest.testmod()
