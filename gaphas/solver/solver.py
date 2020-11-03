"""Constraint solver allows to define constraint between two or more different
variables and keep this constraint always true when one or more of the
constrained variables change. For example, one may want to keep two variables
always equal.

Variables change and at some point of time we want to make all
constraints valid again. This process is called solving constraints.

Gaphas' solver allows to define constraints between Variable
instances.  Constraint classes are defined in `gaphas.constraint`
module.

How It Works
------------
Every constraint contains list of variables and has to be registered
in solver object. Variables change (`Variable.dirty()`,
`Solver.request_resolve()` methods) and their constraints are marked
by solver as dirty. To solve constraints, solver loops through dirty
constraints and asks constraint for
a variable (called weakest variable), which

- has the lowest strength
- or if there are many variables with the same, lowest strength value
  return first unchanged variable with lowest strength
- or if there is no unchanged, then return the first changed with the
  lowest strength

(weakest variable invariants defined above)

Having weakest variable (`constraint.Constraint.weakest()` method)
every constraint is being asked to solve itself
(`constraint.Constraint.solve_for()` method) changing appropriate
variables to make the constraint valid again.
"""
from typing import Union

from gaphas.solver.constraint import Constraint, MultiConstraint
from gaphas.state import observed, reversible_pair


class Solver:
    """Solve constraints.

    A constraint should have accompanying variables.
    """

    def __init__(self):
        # a dict of constraint -> name/variable mappings
        self._constraints = set()
        self._marked_cons = []
        self._solving = False

    constraints = property(lambda s: s._constraints)

    @observed
    def add_constraint(self, constraint: Union[Constraint, MultiConstraint]):
        """Add a constraint. The actual constraint is returned, so the
        constraint can be removed later on.

        Example:

        >>> from gaphas.constraint import EquationConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> len(s._constraints)
        1
        >>> a.value
        0.0
        >>> b.value
        2.0
        >>> len(s._constraints)
        1
        """
        assert constraint, f"No constraint ({constraint})"
        self._constraints.add(constraint)
        self._marked_cons.append(constraint)
        constraint.add_handler(self.request_resolve_constraint)
        return constraint

    @observed
    def remove_constraint(self, constraint: Union[Constraint, MultiConstraint]) -> None:
        """Remove a constraint from the solver.

        >>> from gaphas.constraint import EquationConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> c = s.add_constraint(EquationConstraint(lambda a, b: a -b, a=a, b=b))
        >>> c
        EquationConstraint(<lambda>, a=Variable(0, 20), b=Variable(2, 20))
        >>> s.remove_constraint(c)
        >>> s._marked_cons
        []
        >>> s._constraints
        set()

        Removing a constraint twice has no effect:

        >>> s.remove_constraint(c)
        """
        assert constraint, f"No constraint ({constraint})"
        constraint.remove_handler(self.request_resolve_constraint)
        self._constraints.discard(constraint)
        while constraint in self._marked_cons:
            self._marked_cons.remove(constraint)

    reversible_pair(add_constraint, remove_constraint)

    def request_resolve_constraint(self, c: Constraint) -> None:
        """Request resolving a constraint."""
        if not self._solving:
            if c in self._marked_cons:
                self._marked_cons.remove(c)
            self._marked_cons.append(c)
        else:
            self._marked_cons.append(c)
            if self._marked_cons.count(c) > 100:
                raise JuggleError(
                    f"Variable juggling detected, constraint {c} resolved {self._marked_cons.count(c)} times out of {len(self._marked_cons)}"
                )

    def solve(self) -> None:
        """
        Example:

        >>> from gaphas.constraint import EquationConstraint
        >>> a, b, c = Variable(1.0), Variable(2.0), Variable(3.0)
        >>> s = Solver()
        >>> s.add_constraint(EquationConstraint(lambda a,b: a+b, a=a, b=b))
        EquationConstraint(<lambda>, a=Variable(1, 20), b=Variable(2, 20))
        >>> a.value = 5.0
        >>> s.solve()
        >>> len(s._marked_cons)
        0
        >>> b._value
        -5.0
        >>> s.add_constraint(EquationConstraint(lambda a,b: a+b, a=b, b=c))
        EquationConstraint(<lambda>, a=Variable(-5, 20), b=Variable(3, 20))
        >>> len(s._constraints)
        2
        >>> len(s._marked_cons)
        1
        >>> b._value
        -5.0
        >>> s.solve()
        >>> b._value
        -3.0
        >>> a.value = 10
        >>> s.solve()
        >>> c._value
        10.0
        """
        marked_cons = self._marked_cons
        try:
            self._solving = True

            # Solve each constraint. Using a counter makes it
            # possible to also solve constraints that are marked as
            # a result of other variabled being solved.
            n = 0
            while n < len(marked_cons):
                c = marked_cons[n]
                c.solve()
                n += 1

            self._marked_cons = []
        finally:
            self._solving = False


class JuggleError(AssertionError):
    """Variable juggling exception.

    Raised when constraint's variables are marking each other dirty
    forever.
    """


__test__ = {
    "Solver.add_constraint": Solver.add_constraint,
    "Solver.remove_constraint": Solver.remove_constraint,
}
