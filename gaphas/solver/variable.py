from __future__ import annotations

from typing import Callable, Set, SupportsFloat

from gaphas.state import observed, reversible_property

# epsilon for float comparison
# is simple abs(x - y) > EPSILON enough for canvas needs?
EPSILON = 1e-6

# Variable Strengths:
VERY_WEAK = 0
WEAK = 10
NORMAL = 20
STRONG = 30
VERY_STRONG = 40
REQUIRED = 100


class variable:
    """Easy-to-use drop Variable descriptor.

    >>> class A(object):
    ...     x = variable(varname='_v_x')
    ...     y = variable(STRONG)
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
        """
        Initialize the calculation.

        Args:
            self: (todo): write your description
            strength: (float): write your description
            NORMAL: (todo): write your description
            varname: (str): write your description
        """
        self._strength = strength
        self._varname = varname or f"_variable_{id(self)}"

    def __get__(self, obj, class_=None):
        """
        Return the variable.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            class_: (todo): write your description
        """
        if not obj:
            return self
        try:
            return getattr(obj, self._varname)
        except AttributeError:
            setattr(obj, self._varname, Variable(strength=self._strength))
            return getattr(obj, self._varname)

    def __set__(self, obj, value):
        """
        Set variable value.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            value: (todo): write your description
        """
        try:
            getattr(obj, self._varname).value = float(value)
        except AttributeError:
            v = Variable(strength=self._strength)
            setattr(obj, self._varname, v)
            v.value = value


class Variable:
    """Representation of a variable in the constraint solver.

    Each Variable has a @value and a @strength. In a constraint the weakest
    variables are changed.

    You can even do some calculating with it. The Variable always represents a
    float variable.
    """

    def __init__(self, value: SupportsFloat = 0.0, strength: int = NORMAL):
        """
        Initializes all variables.

        Args:
            self: (todo): write your description
            value: (todo): write your description
            strength: (float): write your description
            NORMAL: (todo): write your description
        """
        self._value = float(value)
        self._strength = strength
        self._handlers: Set[Callable[[Variable], None]] = set()

    def add_handler(self, handler: Callable[[Variable], None]):
        """
        Add a new handler.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
            Callable: (todo): write your description
            Variable: (todo): write your description
        """
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Variable], None]):
        """
        Removes a handler from the event.

        Args:
            self: (todo): write your description
            handler: (todo): write your description
            Callable: (str): write your description
            Variable: (str): write your description
        """
        self._handlers.discard(handler)

    def notify(self):
        """
        Call all registered handlers.

        Args:
            self: (todo): write your description
        """
        for handler in self._handlers:
            handler(self)

    @observed
    def _set_strength(self, strength):
        """
        Sets the dimensions.

        Args:
            self: (todo): write your description
            strength: (int): write your description
        """
        self._strength = strength

    strength = reversible_property(lambda s: s._strength, _set_strength)

    def dirty(self):
        """Mark the variable dirty in both the constraint solver and attached
        constraints.

        Variables are marked dirty also during constraints solving to
        solve all dependent constraints, i.e. two equals constraints
        between 3 variables.
        """
        self.notify()

    @observed
    def set_value(self, value):
        """
        Set the value

        Args:
            self: (todo): write your description
            value: (todo): write your description
        """
        oldval = self._value
        if abs(oldval - value) > EPSILON:
            self._value = float(value)
            self.dirty()

    value = reversible_property(lambda s: s._value, set_value)

    def __str__(self):
        """
        Return a string representation of this object.

        Args:
            self: (todo): write your description
        """
        return f"Variable({self._value:g}, {self._strength:d})"

    __repr__ = __str__

    def __float__(self):
        """
        Returns the float value as float

        Args:
            self: (todo): write your description
        """
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

    def __truediv__(self, other):
        """
        >>> Variable(5) / 4.
        1.25
        >>> Variable(5) / Variable(4)
        1.25
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

    def __rtruediv__(self, other):
        """
        >>> 5 / Variable(4.)
        1.25
        >>> 5. / Variable(4)
        1.25
        """
        return self._value.__rtruediv__(other)
