"""This module contains several flavors of constraint classes.  Each has a
method `Constraint.solve_for(name)` and a method `Constraint.mark_dirty(v)`.
These methods are used by the constraint solver (`solver.Solver`) to set the
variables.

Variables should be of type `solver.Variable`.

See classes' documentation below for constraints description and for
examples of their usage.

EqualsConstraint
    Make 'a' and 'b' equal.
LessThanConstraint
    Ensure one variable stays smaller than another.
CenterConstraint
    Ensures a Variable is kept between two other variables.
EquationConstraint
    Solve a linear equation.
BalanceConstraint
    Keeps three variables in line, maintaining a specific ratio.
LineConstraint
    Solves the equation where a line is connected to a line or side at
    a specific point.

New constraint class should derive from Constraint class abstract
class and implement `Constraint.solve_for(Variable)` method to update
a variable with appropriate value.
"""
import logging
import math
from typing import Dict, Optional, Tuple

from gaphas.position import Position
from gaphas.solver import BaseConstraint, Constraint, Variable

log = logging.getLogger(__name__)


def constraint(
    horizontal: Optional[Tuple[Position, Position]] = None,
    vertical: Optional[Tuple[Position, Position]] = None,
    left_of: Optional[Tuple[Position, Position]] = None,
    above: Optional[Tuple[Position, Position]] = None,
    line: Optional[Tuple[Position, Tuple[Position, Position]]] = None,
    delta: float = 0.0,
    align: Optional[float] = None,
) -> Constraint:
    """Utility (factory) method to create item's internal constraint between
    two positions or between a position and a line.

    Position is a tuple of coordinates, i.e. ``(2, 4)``.

    Line is a tuple of positions, i.e. ``((2, 3), (4, 2))``.

    This method shall not be used to create constraints between
    two different items.

    Created constraint is returned.

    :Parameters:
        horizontal=(p1, p2)
        Keep positions ``p1`` and ``p2`` aligned horizontally.
        vertical=(p1, p2)
        Keep positions ``p1`` and ``p2`` aligned vertically.
        left_of=(p1, p2)
        Keep position ``p1`` on the left side of position ``p2``.
        above=(p1, p2)
        Keep position ``p1`` above position ``p2``.
        line=(p, l)
        Keep position ``p`` on line ``l``.
    """
    cc: Optional[Constraint]
    if horizontal:
        p1, p2 = horizontal
        cc = EqualsConstraint(p1[1], p2[1], delta)
    elif vertical:
        p1, p2 = vertical
        cc = EqualsConstraint(p1[0], p2[0], delta)
    elif left_of:
        p1, p2 = left_of
        cc = LessThanConstraint(p1[0], p2[0], delta)
    elif above:
        p1, p2 = above
        cc = LessThanConstraint(p1[1], p2[1], delta)
    elif line:
        pos, line_l = line
        if align is None:
            cc = LineConstraint(line=line_l, point=pos)
        else:
            cc = LineAlignConstraint(line=line_l, point=pos, align=align, delta=delta)
    else:
        raise ValueError("Constraint incorrectly specified")
    return cc


# is simple abs(x - y) > EPSILON enough for canvas needs?
EPSILON = 1e-6


def _update(variable, value):
    if abs(variable.value - value) > EPSILON:
        variable.value = value


class EqualsConstraint(BaseConstraint):
    """Constraint, which ensures that two arguments ``a`` and ``b`` are equal:

        a + delta = b

    for example
    >>> from gaphas.solver import Variable
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

    def __init__(self, a=None, b=None, delta=0.0):
        super().__init__(a, b, delta)
        self.a = a
        self.b = b
        self.delta = delta

    def solve_for(self, var):
        assert var in (self.a, self.b, self.delta)

        _update(
            *(
                (var is self.a)
                and (self.a, self.b.value - self.delta)
                or (var is self.b)
                and (self.b, self.a.value + self.delta)
                or (self.delta, self.b.value - self.a.value)
            )
        )


class CenterConstraint(BaseConstraint):
    """Simple Constraint, takes three arguments: 'a', 'b' and center. When
    solved, the constraint ensures 'center' is located in the middle of 'a' and
    'b'.

    >>> from gaphas.solver import Variable
    >>> a, b, center = Variable(1.0), Variable(3.0), Variable()
    >>> eq = CenterConstraint(a, b, center)
    >>> eq.solve_for(a)
    >>> a
    Variable(1, 20)
    >>> center
    Variable(2, 20)
    >>> a.value = 10
    >>> eq.solve_for(b)
    >>> b
    Variable(3, 20)
    >>> center
    Variable(6.5, 20)
    """

    def __init__(self, a=None, b=None, center=None):
        super().__init__(a, b, center)
        self.a = a
        self.b = b
        self.center = center

    def solve_for(self, var):
        assert var in (self.a, self.b, self.center)

        v = (self.a.value + self.b.value) / 2.0
        _update(self.center, v)


class LessThanConstraint(BaseConstraint):
    """Ensure ``smaller`` is less than ``bigger``. The variable that is passed
    as to-be-solved is left alone (cause it is the variable that has not been
    moved lately). Instead the other variable is solved.

    >>> from gaphas.solver import Variable
    >>> a, b = Variable(3.0), Variable(2.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b)
    >>> lt.solve_for(a)
    >>> a, b
    (Variable(3, 20), Variable(3, 20))
    >>> b.value = 0.8
    >>> lt.solve_for(b)
    >>> a, b
    (Variable(0.8, 20), Variable(0.8, 20))

    Also minimal delta between two values can be set

    >>> a, b = Variable(10.0), Variable(8.0)
    >>> lt = LessThanConstraint(smaller=a, bigger=b, delta=5)
    >>> lt.solve_for(a)
    >>> a, b
    (Variable(10, 20), Variable(15, 20))
    """

    def __init__(self, smaller=None, bigger=None, delta=0.0):
        super().__init__(smaller, bigger, delta)
        self.smaller = smaller
        self.bigger = bigger
        self.delta = delta

    def solve_for(self, var):
        if self.smaller.value > self.bigger.value - self.delta:
            if var is self.smaller:
                self.bigger.value = self.smaller.value + self.delta
            elif var is self.bigger:
                self.smaller.value = self.bigger.value - self.delta
            elif var is self.delta:
                self.delta.value = self.bigger.value - self.smaller.value


# Constants for the EquationConstraint
ITERLIMIT = 1000  # iteration limit


class EquationConstraint(BaseConstraint):
    """Equation solver using attributes and introspection.

    Takes a function, named arg value (opt.) and returns a Constraint
    object Calling EquationConstraint.solve_for will solve the
    equation for variable ``arg``, so that the outcome is 0.

    >>> from gaphas.solver import Variable
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
        super().__init__(*list(args.values()))
        self._f = f
        self._args: Dict[str, Optional[Variable]] = {}

        # see important note on order of operations in __setattr__ below.
        for arg in f.__code__.co_varnames[0 : f.__code__.co_argcount]:
            self._args[arg] = None
        self._set(**args)

    def __repr__(self):
        argstring = ", ".join(
            [f"{arg}={value}" for (arg, value) in list(self._args.items())]
        )
        if argstring:
            return f"EquationConstraint({self._f.__code__.co_name}, {argstring})"
        else:
            return f"EquationConstraint({self._f.__code__.co_name})"

    def __getattr__(self, name):
        """Used to extract function argument values."""
        self._args[name]
        return self.solve_for(name)

    def __setattr__(self, name, value):
        """Sets function argument values."""
        # Note - once self._args is created, no new attributes can
        # be added to self.__dict__.  This is a good thing as it throws
        # an exception if you try to assign to an arg which is inappropriate
        # for the function in the solver.
        if "_args" in self.__dict__:
            if name in self._args:
                self._args[name] = value
            elif name in self.__dict__:
                self.__dict__[name] = value
            else:
                raise KeyError(name)
        else:
            object.__setattr__(self, name, value)

    def _set(self, **args):
        """Sets values of function arguments."""
        for arg in args:
            self._args[arg]  # raise exception if arg not in _args
            setattr(self, arg, args[arg])

    def solve_for(self, var):
        """Solve this constraint for the variable named 'arg' in the
        constraint."""
        args = {}
        for nm, v in list(self._args.items()):
            assert v
            args[nm] = v.value
            if v is var:
                arg = nm
        v = self._solve_for(arg, args)
        if var.value != v:
            var.value = v

    def _solve_for(self, arg, args):
        """Newton's method solver."""
        # args = self._args
        close_runs = 10  # after getting close, do more passes
        if args[arg]:
            x0 = args[arg]
        else:
            x0 = 1
        if x0 == 0:
            x1 = 1
        else:
            x1 = x0 * 1.1

        def f(x):
            """function to solve."""
            args[arg] = x
            return self._f(**args)

        fx0 = f(x0)
        n = 0
        while True:  # Newton's method loop here
            fx1 = f(x1)
            if fx1 == 0 or x1 == x0:  # managed to nail it exactly
                break
            if abs(fx1 - fx0) < EPSILON:  # very close
                close_flag = True
                if close_runs == 0:  # been close several times
                    break
                else:
                    close_runs -= 1  # try some more
            else:
                close_flag = False
            if n > ITERLIMIT:
                log.warning("Failed to converge; exceeded iteration limit")
                break
            slope = (fx1 - fx0) / (x1 - x0)
            if slope == 0:
                if close_flag:  # we're close but have zero slope, finish
                    break
                else:
                    log.warning("Zero slope and not close enough to solution")
                    break
            x2 = x0 - fx0 / slope  # New 'x1'
            fx0 = fx1
            x0 = x1
            x1 = x2
            n += 1
        return x1


class BalanceConstraint(BaseConstraint):
    """Ensure that a variable ``v`` is between values specified by ``band`` and
    in distance proportional from ``band[0]``.

    Consider

    >>> from gaphas.solver import Variable, WEAK
    >>> a, b, c = Variable(2.0), Variable(3.0), Variable(2.3, WEAK)
    >>> bc = BalanceConstraint(band=(a,b), v=c)
    >>> c.value = 2.4
    >>> c
    Variable(2.4, 10)
    >>> bc.solve_for(c)
    >>> a, b, c
    (Variable(2, 20), Variable(3, 20), Variable(2.3, 10))

    Band does not have to be ``band[0] < band[1]``

    >>> a, b, c = Variable(3.0), Variable(2.0), Variable(2.45, WEAK)
    >>> bc = BalanceConstraint(band=(a,b), v=c)
    >>> c.value = 2.50
    >>> c
    Variable(2.5, 10)
    >>> bc.solve_for(c)
    >>> a, b, c
    (Variable(3, 20), Variable(2, 20), Variable(2.45, 10))
    """

    def __init__(self, band=None, v=None, balance=None):
        super().__init__(band[0], band[1], v)
        self.band = band
        self.balance = balance
        self.v = v

        if self.balance is None:
            self.update_balance()

    def update_balance(self):
        b1, b2 = self.band
        w = b2 - b1
        self.balance = (self.v - b1) / w if w != 0 else 0

    def solve_for(self, var):
        b1, b2 = self.band
        w = b2.value - b1.value
        value = b1.value + w * self.balance
        _update(var, value)


class LineConstraint(BaseConstraint):
    """Ensure a point is kept on a line.

    Attributes:
     - _line: line defined by tuple ((x1, y1), (x2, y2))
     - _point: point defined by tuple (x, y)
    """

    def __init__(self, line, point):
        super().__init__(
            line[0][0], line[0][1], line[1][0], line[1][1], point[0], point[1]
        )

        self._line = line
        self._point = point
        self.update_ratio()

    def update_ratio(self):
        """
        >>> from gaphas.solver import Variable
        >>> line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        >>> point = (Variable(15), Variable(4))
        >>> lc = LineConstraint(line=line, point=point)
        >>> lc.update_ratio()
        >>> lc.ratio_x, lc.ratio_y
        (0.5, 0.2)
        >>> line[1][0].value = 40
        >>> line[1][1].value = 30
        >>> lc.solve_for(point[0])
        >>> lc.ratio_x, lc.ratio_y
        (0.5, 0.2)
        >>> point
        (Variable(20, 20), Variable(6, 20))
        """
        sx, sy = self._line[0]
        ex, ey = self._line[1]
        px, py = self._point

        try:
            self.ratio = float(px.value - sx.value) / float(ex.value - sx.value)
        except ZeroDivisionError:
            try:
                self.ratio = float(py.value - sy.value) / float(ey.value - sy.value)
            except ZeroDivisionError:
                self.ratio = 0.0

    def solve_for(self, var=None):
        self._solve()

    def _solve(self):
        """Solve the equation for the connected_handle.

        >>> from gaphas.solver import Variable
        >>> line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
        >>> point = (Variable(15), Variable(4))
        >>> lc = LineConstraint(line=line, point=point)
        >>> lc.update_ratio()
        >>> lc.solve_for(point[0])
        >>> point
        (Variable(15, 20), Variable(4, 20))
        >>> line[1][0].value = 40
        >>> line[1][1].value =  30
        >>> lc.solve_for(point[0])
        >>> point
        (Variable(20, 20), Variable(6, 20))
        """
        sx, sy = self._line[0]
        ex, ey = self._line[1]
        px, py = self._point

        x = sx.value + (ex.value - sx.value) * self.ratio
        y = sy.value + (ey.value - sy.value) * self.ratio

        _update(px, x)
        _update(py, y)


class PositionConstraint(BaseConstraint):
    """Ensure that point is always in origin position.

    Attributes:
     - _origin: origin position
     - _point: point to be in origin position
    """

    def __init__(self, origin, point):
        super().__init__(origin[0], origin[1], point[0], point[1])

        self._origin = origin
        self._point = point

    def solve_for(self, var=None):
        """Ensure that point's coordinates are the same as coordinates of the
        origin position."""
        x, y = self._origin[0].value, self._origin[1].value
        _update(self._point[0], x)
        _update(self._point[1], y)


class LineAlignConstraint(BaseConstraint):
    """Ensure a point is kept on a line in position specified by align and
    padding information.

    Align is specified as a number between 0 and 1, for example
     0
        keep point at one end of the line
     1
        keep point at other end of the line
     0.5
        keep point in the middle of the line

    Align can be adjusted with `delta` parameter, which specifies the padding of
    the point.

    :Attributes:
     _line
        Line defined by tuple ((x1, y1), (x2, y2)).
     _point
        Point defined by tuple (x, y).
     _align
        Align of point.
     _delta
        Padding of the align.
    """

    def __init__(self, line, point, align=0.5, delta=0.0):
        super().__init__(
            line[0][0], line[0][1], line[1][0], line[1][1], point[0], point[1]
        )

        self._line = line
        self._point = point
        self._align = align
        self._delta = delta

    def solve_for(self, var=None):
        sx, sy = self._line[0]
        ex, ey = self._line[1]
        px, py = self._point
        a = math.atan2(ey.value - sy.value, ex.value - sx.value)

        x = sx.value + (ex.value - sx.value) * self._align + self._delta * math.cos(a)
        y = sy.value + (ey.value - sy.value) * self._align + self._delta * math.sin(a)

        _update(px, x)
        _update(py, y)
