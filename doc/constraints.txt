Constraints
===========
Introduction
------------
There are problems related to canvas items, which can be solved in
`declarative way <http://en.wikipedia.org/wiki/Declarative_programming>`_
allowing for simpler and less error prone implementation of canvas item.

For example, if an item should be a rectangle, then it could be declared
that

- bottom-right vertex should be below and on the right side of top-left
  vertex
- two top rectangle vertices should be always at the same y-axis
- two left rectangle vertices should be always at the same x-axis
- ...

Above rules are constraints, which need to be applied to a rectangular
item. The rules can be satisfied (constraints can be solved) using
`constraint solver <http://en.wikipedia.org/wiki/Constraint_satisfaction_problem>`_.

Gaphas implements its own constraint solver (`gaphas.solver` module).
Items can be constrained using APIs defined in `Canvas` and `Item` classes.

Constraints API
---------------
The `Canvas` class constraints API supports adding a constraint to
constraint solver.  Instance of a constraint has to be created and then
added using `Canvas.add_constraint` method. For example, it allows to
declare that two variables should be equal.

The `Item` class constraint API is more abstract, it allows to constraint
positions, i.e.

- positions of two item handles should be on the same x-axis
- position should be always on a line

If this API does not provide some constraint declaration, then one can
fallback to `Canvas` class constraint API.

Examples
--------
Item API
^^^^^^^^
Canvas API
^^^^^^^^^^

Further Reading
---------------
Theory and examples related to constraint solving

- http://en.wikipedia.org/wiki/Declarative_programming
- http://en.wikipedia.org/wiki/Constraint_satisfaction_problem
- http://norvig.com/sudoku.html

There are other projects providing constraint solvers

- http://adaptagrams.sourceforge.net/
- http://minion.sourceforge.net/
- http://labix.org/python-constraint
- http://www.cs.washington.edu/research/constraints/cassowary/

