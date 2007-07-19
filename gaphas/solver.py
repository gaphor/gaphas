"""
Constraint solver allows to define constraint between two or more different
variables and keep this constraint always true when one or more of the
constrained variables change. For example, one may want to keep two
variables always equal.

Variables change and at some point of time we want to make all constraints
valid again. This process is called solving constraints.

Gaphas' solver allows to define constraints between Variable instances.
Constraint classes are defined in gaphas.constraint module.

How It Works
============
Every constraint contains list of variables and has to be registered in
solver object. Variables change (Variables.dirty, Solver.mark_dirty
methods) and their constraints are marked by solver as dirty. To solve
constraints, solver loops through dirty constraints and asks constraint for
a variable (called weakest variable), which

- has the lowest strength
- or if there are many variables with the same, lowest strength value
  return first unchanged variable with lowest strength
- or if there is no unchanged, then return the first changed with the
  lowest strength

(weakest variable invariants defined above)

Having weakest variable (Constraint.weakest method) every constraint is
being asked to solve itself (Constraint.solv_for method) changing
appropriate variables to make the constraint valid again.
"""

from __future__ import division

__version__ = "$Revision$"
# $HeadURL$

from operator import isCallable
from state import observed, reversible_pair, reversible_property

# epsilon for float comparison
# is simple abs(x - y) > EPSILON enough for canvas needs?
EPSILON = 1e-10

# Variable Strengths:
VERY_WEAK = 0
WEAK = 10
NORMAL = 20
STRONG = 30
VERY_STRONG = 40
REQUIRED = 100


class Variable(object):
    """
    Representation of a variable in the constraint solver.
    Each Variable has a @value and a @strength. Ina constraint the
    weakest variables are changed.
    
    You can even do some calculating with it. The Variable always represents
    a float variable.
    """

    def __init__(self, value=0.0, strength=NORMAL):
        self._value = float(value)
        self._strength = strength

        # These variables are set by the Solver:
        self._solver = None
        self._constraints = set()

    @observed
    def _set_strength(self, strength):
        self._strength = strength
        for c in self._constraints:
            c.create_weakest_list()

    strength = reversible_property(lambda s: s._strength, _set_strength)

    def dirty(self):
        solver = self._solver
        if not solver:
            return
        # variables are marked dirty also during constraints solving to
        # solve all dependent constraints, i.e. two equals constraints
        # between 3 variables
        solver.mark_dirty(self)
        for c in self._constraints:
            c.mark_dirty(self)

    @observed
    def set_value(self, value):
        self._value = float(value)
        self.dirty()

    value = reversible_property(lambda s: s._value, set_value)

    def __str__(self):
        return 'Variable(%g, %d)' % (self._value, self._strength)
    __repr__ = __str__

    def __float__(self):
        return float(self._value)

    def __eq__(self, other):
        """
        >>> Variable(5) == 5
        True
        >>> Variable(5) == 4
        False
        >>> Variable(5) != 5
        False
        """
        return abs(self._value - other) < EPSILON

    def __ne__(self, other):
        """
        >>> Variable(5) != 4
        True
        >>> Variable(5) != 5
        False
        """
        return abs(self._value - other) > EPSILON

    def __gt__(self, other):
        """
        >>> Variable(5) > 4
        True
        >>> Variable(5) > 5
        False
        """
        return self._value.__gt__(float(other))

    def __lt__(self, other):
        """
        >>> Variable(5) < 4
        False
        >>> Variable(5) < 6
        True
        """
        return self._value.__lt__(float(other))

    def __ge__(self, other):
        """
        >>> Variable(5) >= 5
        True
        """
        return self._value.__ge__(float(other))

    def __le__(self, other):
        """
        >>> Variable(5) <= 5
        True
        """
        return self._value.__le__(float(other))

    def __add__(self, other):
        """
        >>> Variable(5) + 4
        9.0
        """
        return self._value.__add__(float(other))

    def __sub__(self, other):
        """
        >>> Variable(5) - 4
        1.0
        >>> Variable(5) - Variable(4)
        1.0
        """
        return self._value.__sub__(float(other))

    def __mul__(self, other):
        """
        >>> Variable(5) * 4
        20.0
        >>> Variable(5) * Variable(4)
        20.0
        """
        return self._value.__mul__(float(other))

    def __floordiv__(self, other):
        """
        >>> Variable(21) // 4
        5.0
        >>> Variable(21) // Variable(4)
        5.0
        """
        return self._value.__floordiv__(float(other))

    def __mod__(self, other):
        """
        >>> Variable(5) % 4
        1.0
        >>> Variable(5) % Variable(4)
        1.0
        """
        return self._value.__mod__(float(other))

    def __divmod__(self, other):
        """
        >>> divmod(Variable(21), 4)
        (5.0, 1.0)
        >>> divmod(Variable(21), Variable(4))
        (5.0, 1.0)
        """
        return self._value.__divmod__(float(other))

    def __pow__(self, other):
        """
        >>> pow(Variable(5), 4)
        625.0
        >>> pow(Variable(5), Variable(4))
        625.0
        """
        return self._value.__pow__(float(other))

    def __div__(self, other):
        """
        >>> Variable(5) / 4.
        1.25
        >>> Variable(5) / Variable(4)
        1.25
        """
        return self._value.__div__(float(other))

    def __truediv__(self, other):
        """
        #>>> from __future__ import division
        >>> Variable(5.) / 4
        1.25
        >>> 10 / Variable(5.)
        2.0
        """
        return self._value.__truediv__(float(other))

    # .. And the other way around:

    def __radd__(self, other):
        """
        >>> 4 + Variable(5)
        9.0
        >>> Variable(4) + Variable(5)
        9.0
        """
        return self._value.__radd__(float(other))

    def __rsub__(self, other):
        """
        >>> 6 - Variable(5)
        1.0
        """
        return self._value.__rsub__(other)

    def __rmul__(self, other):
        """
        >>> 4 * Variable(5)
        20.0
        """
        return self._value.__rmul__(other)

    def __rfloordiv__(self, other):
        """
        >>> 21 // Variable(4)
        5.0
        """
        return self._value.__rfloordiv__(other)

    def __rmod__(self, other):
        """
        >>> 5 % Variable(4)
        1.0
        """
        return self._value.__rmod__(other)

    def __rdivmod__(self, other):
        """
        >>> divmod(21, Variable(4))
        (5.0, 1.0)
        """
        return self._value.__rdivmod__(other)

    def __rpow__(self, other):
        """
        >>> pow(4, Variable(5))
        1024.0
        """
        return self._value.__rpow__(other)

    def __rdiv__(self, other):
        """
        >>> 5 / Variable(4.)
        1.25
        """
        return self._value.__rdiv__(other)

    def __rtruediv__(self, other):
        """
        #>>> from __future__ import division
        >>> 5. / Variable(4)
        1.25
        """
        return self._value.__rtruediv__(other)


class Solver(object):
    """
    Solve constraints. A constraint should have accompanying
    variables.
    """

    def __init__(self):
        # a dict of constraint -> name/variable mappings
        self._constraints = set()
        self._marked_cons = []
        self._solving = False

    def mark_dirty(self, *variables):
        """
        Mark a variable as "dirty". This means it it solved the next time
        the constraints are resolved.

        Example:
        >>> from constraint import EquationConstraint
        >>> a, b, c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s = Solver()
        >>> c_eq = EquationConstraint(lambda a,b: a+b, a=a, b=b)
        >>> s.add_constraint(c_eq)
        EquationConstraint(<lambda>, a=Variable(1, 20), b=Variable(2, 20))
        >>> c_eq._weakest
        [Variable(1, 20), Variable(2, 20)]
        >>> s._marked_cons
        [EquationConstraint(<lambda>, a=Variable(1, 20), b=Variable(2, 20))]
        >>> a.value=5.0
        >>> c_eq.weakest()
        Variable(2, 20)
        >>> b.value=2.0
        >>> c_eq.weakest()
        Variable(5, 20)
        >>> a.value=5.0
        >>> c_eq.weakest()
        Variable(2, 20)
        """
        for variable in variables:
            for c in variable._constraints:
                if not self._solving:
                    if c in self._marked_cons:
                        self._marked_cons.remove(c)
                    self._marked_cons.append(c)
                else:
                    self._marked_cons.append(c)
                    if __debug__:
                        if self._marked_cons.count(c) > 100:
                            raise JuggleError, 'Variable juggling detected, constraint %s' % c


    def request_resolve(self, c):
        """
        Request resolving of the constraint.
        """
        self._marked_cons.append(c)


    @observed
    def add_constraint(self, constraint):
        """
        Add a constraint.
        The actual constraint is returned, so the constraint can be removed
        later on.

        Example:
        >>> from constraint import EquationConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> len(s._constraints)
        1
        >>> a.value
        0.0
        >>> b.value
        2.0
        >>> len(s._constraints)
        1
        """
        #if isCallable(constraint):
        #    from constraint import EquationConstraint
        #    constraint = EquationConstraint(constraint)
        #constraint.set(**variables)
        #print constraint
        self._constraints.add(constraint)
        self._marked_cons.append(constraint)
        for v in constraint.variables():
            v._constraints.add(constraint)
            v._solver = self
        #print 'added constraint', constraint
        return constraint

    @observed
    def remove_constraint(self, constraint):
        """ Remove a constraint from the solver
        >>> from constraint import EquationConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> c = s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        >>> c
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> s.remove_constraint(c)
        >>> s._marked_cons
        []
        >>> s._constraints
        set([])

        Removing a constraint twice has no effect:
        >>> s.remove_constraint(c)

        """
        for v in constraint.variables():
            v._constraints.discard(constraint)
        self._constraints.discard(constraint)
        if constraint in self._marked_cons:
            del self._marked_cons[self._marked_cons.index(constraint)]

    reversible_pair(add_constraint, remove_constraint)

    def constraints_with_variable(self, variable):
        """
        Return an iterator of constraints that work with variable.
        The variable in question should be exposed by the constraints
        variables() method.

        >>> from constraint import EquationConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> len(s._constraints)
        2
        >>> for c in s.constraints_with_variable(a): print c
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        """
        # use a copy of the original set, so constraints may be deleted in the
        # meantime.
        for c in set(self._constraints):
            if variable in c.variables():
                yield c


    def solve(self):
        """
        Example:
        >>> from constraint import EquationConstraint
        >>> a, b, c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s = Solver()
        >>> s.add_constraint(EquationConstraint(lambda a,b: a+b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(1, 20), b=Variable(2, 20))
        >>> a.value = 5.0
        >>> s.solve()
        >>> len(s._marked_cons)
        0
        >>> b._value
        -5.0
        >>> s.add_constraint(EquationConstraint(lambda a,b: a+b, a=b, b=c))
        EquationConstraint(<lambda>, a=Variable(-5, 20), b=Variable(3, 20))
        >>> len(s._constraints)
        2
        >>> len(s._marked_cons)
        1
        >>> b._value
        -5.0
        >>> s.solve()
        >>> b._value
        -3.0
        >>> a.value = 10
        >>> s.solve()
        >>> c._value
        10.0
        """
        constraints = self._constraints
        marked_cons = self._marked_cons
        try:
            self._solving = True

            # Solve each constraint. Using a counter makes it
            # possible to also solve constraints that are marked as
            # a result of other variabled being solved.
            n = 0
            while n < len(marked_cons):
                c = marked_cons[n]
                if not c.disabled:
                    wvar = c.weakest()
                    c.solve_for(wvar)
                n += 1

            self._marked_cons = []
        finally:
            self._solving = False

class solvable(object):
    """
    Easy-to-use drop Variable descriptor.

    >>> class A(object):
    ...     x = solvable(varname='_v_x')
    ...     y = solvable(STRONG)
    ...     def __init__(self):
    ...         self.x = 12
    >>> a = A()
    >>> a.x
    Variable(12, 20)
    >>> a._v_x
    Variable(12, 20)
    >>> a.x = 3
    >>> a.x 
    Variable(3, 20)
    >>> a.y 
    Variable(0, 30)
    """

    def __init__(self, strength=NORMAL, varname=None):
        self._strength = strength
        self._varname = varname or '_variable_%x' % id(self)

    def __get__(self, obj, class_=None):
        if not obj:
            return self
        try:
            return getattr(obj, self._varname)
        except AttributeError:
            setattr(obj, self._varname, Variable(strength=self._strength))
            return getattr(obj, self._varname)

    def __set__(self, obj, value):
        try:
            getattr(obj, self._varname).value = float(value)
        except AttributeError:
            v = Variable(strength=self._strength)
            setattr(obj, self._varname, v)
            v.value = value




class JuggleError(AssertionError):
    """
    Variable juggling exception. Raised when constraint's variables are
    marking each other dirty forever.
    """


__test__ = {
    'Solver.add_constraint': Solver.add_constraint,
    'Solver.remove_constraint': Solver.remove_constraint,
    }


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
