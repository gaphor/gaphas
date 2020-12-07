Variables and Position
======================


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