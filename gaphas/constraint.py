"""
This module contains several flavors of constraint solver classes.
Each has a method solve_for(name) and a method set(\*\*kwds). These methods
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
from __future__ import division
import operator

__version__ = "$Revision$"
# $HeadURL$

class Constraint(object):
    """
    Constraint base class.

    - _variables - list of all variables
    - _weakest   - list of weakest variables
    """
    disabled = False

    def __init__(self, *variables):
        """
        Create new constraint, register all variables, and find weakest
        variables.
        """
        self._variables = []
        for v in variables:
            self._variables.append(v)
        # Python 2.5:
        #v = min(self._variables, key=operator.attrgetter('strength'))
        #strength = v.strength
        strength = min(map(operator.attrgetter('strength'), self._variables))
        self._weakest = []
        for v in self._variables:
            if strength == v.strength:
                self._weakest.append(v)


    def variables(self):
        """
        Return an iterator which iterates over the variables that are
        held by this constraint.
        """
        return self._variables


    def weakest(self):
        """
        Return the weakest variable. The weakest variable should be always
        as first element of Constraint._weakest list.
        """
        return self._weakest[0]


    def mark_dirty(self, v):
        """
        Mark variable v dirty and if possible move it to the end of
        Constraint._weakest list to maintain weakest variable invariants
        (see gaphas.solver module documentation).
        """
        if v is self.weakest():
            self._weakest.remove(v)
            self._weakest.append(v)


    def solve_for(self, var):
        """
        Solve the constraint for a given variable.
        The variable itself is updated.
        """
        raise NotImplemented



class EqualsConstraint(Constraint):
    """
    Simple Constraint, takes two arguments: 'a' and 'b'. When solved the
    attribute passed to solve_for() is set equal to the other.

    >>> from solver import Variable
    >>> a, b = Variable(1.0), Variable(2.0)
    >>> eq = EqualsConstraint(a, b)
    >>> eq.solve_for(a)
    >>> a
    Variable(2, 20)
    >>> a.value = 10.8
    >>> eq.solve_for(b)
    >>> b
    Variable(10.8, 20)
    """

    def __init__(self, a=None, b=None):
        super(EqualsConstraint, self).__init__(a, b)
        self.a = a
        self.b = b

    def solve_for(self, var):
        assert var in (self.a, self.b)

        if var is self.a:
            self.a.value = self.b.value
        else:
            self.b.value = self.a.value


class LessThanConstraint(Constraint):
    """
    Ensure @smaller is less than @bigger. The variable that is passed
    as to-be-solved is left alone (cause it is the variable that has not
    been moved lately). Instead the other variable is solved.

    >>> from solver import Variable
    >>> a, b = Variable(3.0), Variable(2.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b)
    >>> lt.solve_for(a)
    >>> a, b
    (Variable(3, 20), Variable(3, 20))
    >>> b.value = 0.8
    >>> lt.solve_for(b)
    >>> a, b
    (Variable(0.8, 20), Variable(0.8, 20))
    """

    def __init__(self, smaller=None, bigger=None):
        super(LessThanConstraint, self).__init__(smaller, bigger)
        self.smaller = smaller
        self.bigger = bigger

    def solve_for(self, var):
        if self.smaller.value > self.bigger.value:
            if var is self.smaller:
                self.bigger.value = self.smaller.value
            elif var is self.bigger:
                self.smaller.value = self.bigger.value


# Constants for the EquationConstraint
TOL = 0.0000001      # tolerance
ITERLIMIT = 1000        # iteration limit

class EquationConstraint(Constraint):
    """
    Equation solver using attributes and introspection.

    Takes a function, named arg value (opt.) and returns a Constraint object
    Calling EquationConstraint.solve_for will solve the equation for
    variable @arg, so that the outcome is 0.

    >>> from solver import Variable
    >>> a, b, c = Variable(), Variable(4), Variable(5)
    >>> cons = EquationConstraint(lambda a, b, c: a + b - c, a=a, b=b, c=c)
    >>> cons.solve_for(a)
    >>> a
    Variable(1, 20)
    >>> a.value = 3.4
    >>> cons.solve_for(b)
    >>> b
    Variable(1.6, 20)

    From: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/303396
    """
    
    def __init__(self, f, **args):
        super(EquationConstraint, self).__init__(*args.values())
        self._f = f
        self._args = {}
        # see important note on order of operations in __setattr__ below.
        for arg in f.func_code.co_varnames[0:f.func_code.co_argcount]:
            self._args[arg] = None
        self._set(**args)

    def __repr__(self):
        argstring = ', '.join(['%s=%s' % (arg, str(value)) for (arg, value) in
                             self._args.items()])
        if argstring:
            return 'EquationConstraint(%s, %s)' % (self._f.func_code.co_name, argstring)
        else:
            return 'EquationConstraint(%s)' % self._f.func_code.co_name

    def __getattr__(self, name):
        """
        Used to extract function argument values.
        """
        self._args[name]
        return self.solve_for(name)

    def __setattr__(self, name, value):
        """
        Sets function argument values.
        """
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

    def _set(self, **args):
        """
        Sets values of function arguments.
        """
        for arg in args:
            self._args[arg]  # raise exception if arg not in _args
            setattr(self, arg, args[arg])


    def solve_for(self, var):
        """
        Solve this constraint for the variable named 'arg' in the
        constraint.
        """
        args = {}
        for nm, v in self._args.items():
            args[nm] = v.value
            if v is var: arg = nm
        var.value = self._solve_for(arg, args)

    def _solve_for(self, arg, args):
        """
        Newton's method solver
        """
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
        return x1


class LineConstraint(Constraint):
    """
    Ensure a point is kept on a line, taking into account item
    specific coordinates.

    #>>> from solver import Variable
    #>>> a, b = Variable(3.0), Variable(2.0)
    #>>> lt = LessThanConstraint(smaller=a, bigger=b)
    #>>> lt.solve_for('smaller')
    #>>> a, b
    #(Variable(3, 20), Variable(3, 20))
    #>>> b.value = 0.8
    #>>> lt.solve_for('bigger')
    #>>> a, b
    #(Variable(0.8, 20), Variable(0.8, 20))
    """

    def __init__(self, canvas, connect_to_item, handle_1, handle_2,
                 connected_item, connected_handle):
        super(LineConstraint, self).__init__(handle_1.x,
                handle_1.y,
                handle_2.x,
                handle_2.y,
                connected_handle.x,
                connected_handle.y)

        self._canvas = canvas
        self._connect_to_item = connect_to_item
        self._handle_1 = handle_1
        self._handle_2 = handle_2
        self._connected_item = connected_item
        self._connected_handle = connected_handle
        self.update_ratio()


    def update_ratio(self):
        """
        >>> from item import Handle, Item
        >>> from canvas import Canvas
        >>> c = Canvas()
        >>> i1, i2 = Item(), Item()
        >>> c.add(i1)
        >>> c.add(i2)
        >>> c.update_now()
        >>> h1, h2, h3 = Handle(0, 0), Handle(30, 20), Handle(15, 4)
        >>> eq = LineConstraint(c, i1, h1, h2, i2, h3)
        >>> eq.ratio_x, eq.ratio_y
        (0.5, 0.20000000000000001)
        >>> h2.pos = 40, 30
        >>> eq.solve_for(h3.x)
        >>> eq.ratio_x, eq.ratio_y
        (0.5, 0.20000000000000001)
        >>> h3.pos
        (Variable(20, 20), Variable(6, 20))
        """
        start = self._handle_1
        end = self._handle_2
        point = self._connected_handle

        get_i2w = self._canvas.get_matrix_i2w

        sx, sy = get_i2w(self._connect_to_item).transform_point(start.x, start.y)
        ex, ey = get_i2w(self._connect_to_item).transform_point(end.x, end.y)
        px, py = get_i2w(self._connected_item).transform_point(point.x, point.y)

        try:
            self.ratio_x = float(px - sx) / float(ex - sx)
        except ZeroDivisionError:
            self.ratio_x = 0.0
        try:
            self.ratio_y = float(py - sy) / float(ey - sy)
        except ZeroDivisionError:
            self.ratio_y = 0.0
        
    def solve_for(self, var=None):
        self._solve()

    def _solve(self):
        """
        Solve the equation for the connected_handle.
        >>> from item import Handle, Item
        >>> from canvas import Canvas
        >>> c = Canvas()
        >>> i1, i2 = Item(), Item()
        >>> c.add(i1)
        >>> c.add(i2)
        >>> c.update_now()
        >>> h1, h2, h3 = Handle(0, 0), Handle(30, 20), Handle(15, 4)
        >>> eq = LineConstraint(c, i1, h1, h2, i2, h3)
        >>> eq.solve_for(h3.x)
        >>> h3.pos
        (Variable(15, 20), Variable(4, 20))
        >>> h2.pos = 40, 30
        >>> eq.solve_for(h3.x)
        >>> h3.pos
        (Variable(20, 20), Variable(6, 20))
        >>> i2.matrix.translate(5,5)
        >>> i2.request_update()
        >>> c.update_now()
        >>> eq.solve_for(h3.x)
        >>> h3.pos
        (Variable(15, 20), Variable(1, 20))
        """
        start = self._handle_1
        end = self._handle_2
        point = self._connected_handle

        get_i2w = self._canvas.get_matrix_i2w
        get_w2i = self._canvas.get_matrix_w2i

        sx, sy = get_i2w(self._connect_to_item).transform_point(start.x, start.y)
        ex, ey = get_i2w(self._connect_to_item).transform_point(end.x, end.y)

        px = sx + (ex - sx) * self.ratio_x
        py = sy + (ey - sy) * self.ratio_y

        point.x.value, point.y.value = \
            get_w2i(self._connected_item).transform_point(px, py)
        # Need to queue a redraw of the manipulated item.
        #view.queue_draw_item(self._connected_item, handles=True)
        self._canvas.request_update(self._connected_item)


if __name__ == '__main__':
    import doctest, sys
    sys.path.append('..')
    doctest.testmod()

# vim:sw=4:et:ai
