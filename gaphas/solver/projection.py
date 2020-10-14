from __future__ import annotations

from typing import Callable, Set, Union

from gaphas.solver.variable import Variable


class Projection:
    """Projections are used to convert values from one space to another, e.g.
    from Canvas to Item space or visa versa.

    In order to be a Projection the ``value`` and ``strength``
    properties should be implemented and a method named ``variable()``
    should be present.

    Projections should inherit from this class.

    Projections may be nested.

    This default implementation projects a variable to it's own:

    >>> v = Variable(4.0)
    >>> v
    Variable(4, 20)
    >>> p = Projection(v)
    >>> p.value
    4.0
    >>> p.value = -1
    >>> p.value
    -1.0
    >>> v.value
    -1.0
    >>> p.strength
    20
    >>> p.variable()
    Variable(-1, 20)
    """

    def __init__(self, var: Union[Projection, Variable]):
        self._var = var
        self._handlers: Set[Callable[[Projection], None]] = set()

    def _set_value(self, value):
        self._var.value = value

    value = property(lambda s: s._var.value, _set_value)

    strength = property(lambda s: s._var.strength)

    def variable(self):
        """Return the variable owned by the projection."""
        return self._var

    def add_handler(self, handler: Callable[[Projection], None]):
        if not self._handlers:
            self._var.add_handler(self._propagate)
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Projection], None]):
        self._handlers.discard(handler)
        if not self._handlers:
            self._var.remove_handler(self._propagate)

    def notify(self):
        for handler in self._handlers:
            handler(self)

    def _propagate(self, _variable):
        self.notify()

    def __float__(self):
        return float(self.variable()._value)

    def __str__(self):
        return f"{self.__class__.__name__}({self.variable()})"

    __repr__ = __str__
