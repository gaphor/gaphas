
from __future__ import division

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
    
    You can even do some calculating with it. The Variable always represents
    a float variable.
    """

    def __init__(self, value=0.0, strength=NORMAL):
        self._value = float(value)
        self._strength = strength

        # These variables are set by the Solver:
        self._solver = None
        self._constraints = set()

    strength = property(lambda s: s._strength)

    def set_value(self, value):
        self._value = float(value)
        if self._solver:
            self._solver.mark_dirty(self)

    value = property(lambda s: s._value, set_value)

    def __str__(self):
        return 'Variable(%g, %d)' % (self._value, self._strength)
    __repr__ = __str__

    def __float__(self):
        return float(self._value)

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
    """Solve constraints. A constraint should have accompanying
    variables.
    """

    def __init__(self):
        # a dict of constraint -> name/variable mappings
        self._constraints = {}
        self._marked_vars = []
        self._marked_cons = []
        self._solving = False

    def mark_dirty(self, variable):
        """Mark a variable as "dirty". This means it it solved the next time
        the constraints are resolved.

        Example:
        >>> a,b,c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s=Solver()
        >>> s.add_constraint(lambda a,b: a+b, a=a, b=b)
        Constraint(<lambda>, a=None, b=None)
        >>> s._marked_vars
        []
        >>> s._marked_cons
        [Constraint(<lambda>, a=None, b=None)]
        >>> a.value=5.0
        >>> s._marked_vars
        [Variable(5, 20)]
        >>> b.value=2.0
        >>> s._marked_vars
        [Variable(5, 20), Variable(2, 20)]
        >>> a.value=5.0
        >>> s._marked_vars
        [Variable(2, 20), Variable(5, 20)]
        """
        if not self._solving:
            if variable in self._marked_vars:
                self._marked_vars.remove(variable)
            self._marked_vars.append(variable)
        elif variable not in self._marked_vars:
            self._marked_vars.append(variable)

        for c in variable._constraints:
            if not self._solving:
                if c in self._marked_cons:
                    self._marked_cons.remove(c)
                self._marked_cons.append(c)
            elif c not in self._marked_cons:
                self._marked_cons.append(c)

    def add_constraint(self, constraint, **variables):
        """Add a constraint.
        The actual constraint is returned, so the constraint can be removed
        later on.

        Example:
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(lambda a, b: a -b, a=a, b=b)
        Constraint(<lambda>, a=None, b=None)
        >>> len(s._constraints)
        1
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
        #print 'added constraint', constraint
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
        ('b', Variable(2, 20))
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
        Constraint(<lambda>, a=None, b=None)
        >>> a.value=5.0
        >>> s.solve()
        >>> len(s._marked_cons)
        0
        >>> b._value
        -5.0
        >>> s.add_constraint(lambda a,b: a+b, a=b, b=c)
        Constraint(<lambda>, a=None, b=None)
        >>> len(s._constraints)
        2
        >>> len(s._marked_cons)
        1
        >>> s.solve()
        >>> b._value
        -5.0
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
            while n < len(self._marked_cons):
                c = marked_cons[n]
                wname, wvar = self.weakest_variable(constraints[c])
                xx = {}
                for nm, v in constraints[c].items():
                  xx[nm] = v.value
                c.set(**xx)
                #print 'solving', c, 'for', wname, n, len(marked_cons)
                wvar.value = c.solve_for(wname)
                n += 1

            self._marked_cons = []
            self._marked_vars = []
        finally:
            self._solving = False

class solvable(object):
    """Easy-to-use drop Variable descriptor.

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


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
