Constraint Solver
=================

Gaphas' constraint solver can be consider the heart of the Canvas (The Canvas instance holds and orders the items that are drawn on it and in the end will be displayed to the user).

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

------

The Solver can be found at: https://github.com/gaphor/gaphas/blob/master/gaphas/solver.py, along with Variables and Projections.
