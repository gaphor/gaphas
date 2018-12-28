Constraint Solver
=================

Gaphas' constraint solver can be consider the hart of the Canvas (The Canvas instance holds and orders the items that are drawn on it and in the end will be displayed to the user).

The constraint solver ('solver' for short) is called during the update of the canvas.

A solver contains a set of constraints. Each constraint in itself is pretty straightforward (e.g. variable ''a'' equals variable ''b''). Did I say variable? Yes I did. Let's start at the bottom and work our way to the solver.

A Variable is a simple class, contains a value. It behaves like a ''float'' in many ways. There is one typical thing about Variables: they can be added to Constraints.

A Constraint is an equation. The trick is to make all constraints true when solving a set of constraints. That can be pretty tricky, since a Variable can play a role in more than one Constraint. Constraint solving is governed by the Solver (ah, there it is).

Constraints are instances of Constraint class (more specific: subclasses of the Constraint class). A Constraint can perform a specific trick: e.g. centre one Variable between two other Variables or make one Variable equal to another Variable.

It's the Solver's job to make sure all constraint are true in the end. In some cases this means a constraint needs to be resolved twice, but the Solver sees to it that no deadlocks occur.

Variables
---------

When a variable is assigned a value it marks itself ''dirty''. As a result it will be resolved the next time the solver is asked to.

Each variable has a specific ''strength''. String variables can not be changed by weak variables, but weak variables can change when a new value is assigned to a stronger variable. The Solver always tries to solve a constraint for the weakest variable. If two variables have equal strength, however, the variable that is most recently changed is considered slightly stronger than the not (or earlier) changed variable.

Projections
-----------

There's one special thing about Variables: since each item has it's own coordinate system ((0, 0) point, handy when the item is rendered), it's pretty hard to make sure (for example) a line can connect to a box and ''stays'' connected, even when the box is dragged around. How can such a constraint be maintained? This is where Projections come into play. A Projection can be used to project a variable on another space (read: coordinate system).

The default projection (to canvas coordinates) is located in `gaphas.canvas` and is known as `CanvasProjection`.

When a constraint contains projections, it is most likely that this constraint connects two items together. At least the constraint is not entirely bound to the item's coordinate space. This knowledge is used when an item is moved. A move operation typically only requires a change in coordinates, relative to the item's parent item (this is why having a (0,0) point per item is so handy). This means that constraints local to the item not not need to be resolved. Constraints with links outside the item's space should be solved though. Projections play an important role in determining which constraints should be resolved.

------

The Solver can be found at: http://github.com/amolenaar/gaphas/trees/blobs/gaphas/solver.py, along with Variables and Projections.

