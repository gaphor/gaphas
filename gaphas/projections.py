class Projection:
    """
    Projections are used to convert values from one space to another,
    e.g. from Canvas to Item space or visa versa.

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
        """
        Return the variable owned by the projection.
        """
        return self._var

    def __float__(self):
        return float(self.variable()._value)

    def __str__(self):
        return f"{self.__class__.__name__}({self.variable()})"

    __repr__ = __str__


class VariableProjection(Projection):
    """
    Project a single `solver.Variable` to another space/coordinate system.

    The value has been set in the "other" coordinate system. A
    callback is executed when the value changes.

    It's a simple Variable-like class, following the Projection protocol:

    >>> def notify_me(val):
    ...     print('new value', val)
    >>> p = VariableProjection('var placeholder', 3.0, callback=notify_me)
    >>> p.value
    3.0
    >>> p.value = 6.5
    new value 6.5
    """

    def __init__(self, var, value, callback):
        self._var = var
        self._value = value
        self._callback = callback

    def _set_value(self, value):
        self._value = value
        self._callback(value)

    value = property(lambda s: s._value, _set_value)

    def variable(self):
        return self._var


class CanvasProjection:
    """
    Project a point as Canvas coordinates.  Although this is a
    projection, it behaves like a tuple with two Variables
    (Projections).

    >>> canvas = Canvas()
    >>> from gaphas.item import Element
    >>> a = Element()
    >>> canvas.add(a)
    >>> a.matrix.translate(30, 2)
    >>> canvas.request_matrix_update(a)
    >>> canvas.update_now()
    >>> canvas.get_matrix_i2c(a)
    cairo.Matrix(1, 0, 0, 1, 30, 2)
    >>> p = CanvasProjection(a.handles()[2].pos, a)
    >>> a.handles()[2].pos
    <Position object on (10, 10)>
    >>> p[0].value
    40.0
    >>> p[1].value
    12.0
    >>> p[0].value = 63
    >>> p._point
    <Position object on (33, 10)>

    When the variables are retrieved, new values are calculated.
    """

    def __init__(self, point, item):
        self._point = point
        self._item = item

    def _on_change_x(self, value):
        item = self._item
        self._px = value
        self._point.x.value, self._point.y.value = item.canvas.get_matrix_c2i(
            item
        ).transform_point(value, self._py)
        item.canvas.request_update(item, matrix=False)

    def _on_change_y(self, value):
        item = self._item
        self._py = value
        self._point.x.value, self._point.y.value = item.canvas.get_matrix_c2i(
            item
        ).transform_point(self._px, value)
        item.canvas.request_update(item, matrix=False)

    def _get_value(self):
        """
        Return two delegating variables. Each variable should contain
        a value attribute with the real value.
        """
        item = self._item
        x, y = self._point.x, self._point.y
        self._px, self._py = item.canvas.get_matrix_i2c(item).transform_point(x, y)
        return self._px, self._py

    pos = property(
        lambda self: list(
            map(
                VariableProjection,
                self._point,
                self._get_value(),
                (self._on_change_x, self._on_change_y),
            )
        )
    )

    def __getitem__(self, key):
        # Note: we can not use bound methods as callbacks, since that will
        #       cause pickle to fail.
        return self.pos[key]

    def __iter__(self):
        return iter(self.pos)
