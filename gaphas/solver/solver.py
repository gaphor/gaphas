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

from __future__ import annotations

import functools
from collections.abc import Callable, Collection

from gaphas.solver.constraint import Constraint, ContainsConstraints


class Solver:
    """Solve constraints.

    A constraint should have accompanying variables.
    """

    def __init__(self, resolve_limit: int = 16) -> None:
        # a dict of constraint -> name/variable mappings
        self._constraints: set[Constraint] = set()
        self._marked_cons: list[Constraint] = []
        self._solving = False
        self._resolve_limit = resolve_limit
        self._handlers: set[Callable[[Constraint], None]] = set()

    def add_handler(self, handler: Callable[[Constraint], None]) -> None:
        """Add a callback handler, triggered when a constraint is resolved."""
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Constraint], None]) -> None:
        """Remove a previously assigned handler."""
        self._handlers.discard(handler)

    def _notify(self, constraint: Constraint) -> None:
        my_constraint = self._find_containing_constraint(constraint)
        for handler in self._handlers:
            handler(my_constraint)

    @functools.lru_cache()
    def _find_containing_constraint(self, constraint: Constraint) -> Constraint:
        return find_containing_constraint(constraint, self._constraints) or constraint

    @property
    def constraints(self) -> Collection[Constraint]:
        return self._constraints

    def add_constraint(self, constraint: Constraint) -> Constraint:
        """Add a constraint. The actual constraint is returned, so the
        constraint can be removed later on.

        Example:

        >>> from gaphas.constraint import EqualsConstraint
        >>> s = Solver()
        >>> a, b = Variable(), Variable(2.0)
        >>> s.add_constraint(EqualsConstraint(a, b))
        EqualsConstraint(a=Variable(0, 20), b=Variable(2, 20))
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

    def remove_constraint(self, constraint: Constraint) -> None:
        """Remove a constraint from the solver."""
        assert constraint, f"No constraint ({constraint})"
        constraint.remove_handler(self.request_resolve_constraint)
        self._constraints.discard(constraint)
        while constraint in self._marked_cons:
            self._marked_cons.remove(constraint)

    def request_resolve_constraint(self, c: Constraint) -> None:
        """Request resolving a constraint."""
        if not self._solving:
            if c in self._marked_cons:
                self._marked_cons.remove(c)
            self._marked_cons.append(c)
        elif self._marked_cons.count(c) < self._resolve_limit:
            self._marked_cons.append(c)

    @property
    def needs_solving(self) -> bool:
        """Return if there are constraints that need solving."""
        return bool(self._marked_cons)

    def solve(self) -> None:  # sourcery skip: while-to-for
        """Solve (dirty) constraints."""
        # NB. marked_cons is updated during the solving process
        marked_cons = self._marked_cons
        notify = self._notify
        try:
            self._solving = True

            # Solve each constraint. Using a counter makes it
            # possible to also solve constraints that are marked as
            # a result of other variables being solved.
            # sourcery: skip
            n = 0
            while n < len(marked_cons):
                c = marked_cons[n]
                c.solve()
                notify(c)
                n += 1

            self._marked_cons = []
        finally:
            self._solving = False


def find_containing_constraint(
    constraint: Constraint, constraints: Collection[Constraint]
) -> Constraint | None:
    if constraint in constraints:
        return constraint

    return next(
        (
            find_containing_constraint(cs, constraints)
            for cs in constraints
            if isinstance(cs, ContainsConstraints)
            and find_containing_constraint(constraint, cs.constraints)
        ),
        None,
    )
