Variables and Position
======================

The most basic class for a solvable value is ``Variable``. It acts a lot like a ``float``, which makes
it easy to work with.

Next to that there's Position, which is a coordinate ``(x, y)`` defined by two variables.

To support connections between variables, a ``MatrixProjection`` class is available. It translates
a position to a common coordinate space, based on ``Item.matrix_i2c``. Normally, it's only ``Ports`` that
deal with item-to-common translation of positions.

.. autoclass:: gaphas.solver.Variable
   :members:

Variables can have different strengths. The higher the number, the stronger the variable.
Variables can be ``VERY_WEAK`` (0), up to ``REQUIRED`` (100).
Other constants are
``WEAK`` (10)
``NORMAL`` (20)
``STRONG`` (30), and
``VERY_STRONG`` (40).


.. autofunction:: gaphas.solver.variable


.. autoclass:: gaphas.position.Position


.. autoclass:: gaphas.position.MatrixProjection
