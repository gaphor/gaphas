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


class Variable:
    """Representation of a variable in the constraint solver.

    Each Variable has a @value and a @strength. In a constraint the weakest
    variables are changed.

    You can even do some calculating with it. The Variable always represents a
    float variable.
    """

    def __init__(self, value: SupportsFloat = 0.0, strength: int = NORMAL):
        self._value = float(value)
        self._strength = strength
        self._handlers: Set[Callable[[Variable], None]] = set()

    def add_handler(self, handler: Callable[[Variable], None]):
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Variable], None]):
        self._handlers.discard(handler)

    def notify(self):
        for handler in self._handlers:
            handler(self)

    def __hash__(self):
        return object.__hash__(self)

    @observed
    def _set_strength(self, strength):
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
        oldval = self._value
        if abs(oldval - value) > EPSILON:
            self._value = float(value)
            self.dirty()

    value = reversible_property(lambda s: s._value, set_value)

    def __str__(self):
        return f"Variable({self._value:g}, {self._strength:d})"

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
