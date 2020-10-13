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

    def __init__(self, var):
        self._var = var

    def _set_value(self, value):
        self._var.value = value

    value = property(lambda s: s._var.value, _set_value)

    strength = property(lambda s: s._var.strength)

    def variable(self):
        """Return the variable owned by the projection."""
        return self._var

    def __float__(self):
        return float(self.variable()._value)

    def __str__(self):
        return f"{self.__class__.__name__}({self.variable()})"

    __repr__ = __str__
