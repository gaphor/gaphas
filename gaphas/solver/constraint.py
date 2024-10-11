from __future__ import annotations

from typing import Callable, Collection, Hashable, Protocol, runtime_checkable

from gaphas.solver.variable import Variable


@runtime_checkable
class Constraint(Protocol, Hashable):
    def add_handler(self, handler: Callable[[Constraint], None]) -> None: ...

    def remove_handler(self, handler: Callable[[Constraint], None]) -> None: ...

    def solve(self) -> None: ...


@runtime_checkable
class ContainsConstraints(Protocol):
    @property
    def constraints(self) -> Collection[Constraint]: ...


class BaseConstraint:
    """Constraint base class.

    - variables - list of all variables
    - weakest   - list of weakest variables
    """

    def __init__(self, *variables):
        """Create new constraint, register all variables, and find weakest
        variables.

        Any value can be added. It is assumed to be a variable if it has
        a 'strength' attribute.
        """
        self._variables = [v for v in variables if hasattr(v, "strength")]

        strength = min(v.strength for v in self._variables)
        # manage weakest based on id, so variables are uniquely identifiable
        self._weakest = [(id(v), v) for v in self._variables if v.strength == strength]
        self._handlers: set[Callable[[Constraint], None]] = set()

    def variables(self):
        """Return an iterator which iterates over the variables that are held
        by this constraint."""
        return self._variables

    def add_handler(self, handler: Callable[[Constraint], None]) -> None:
        if not self._handlers:
            for v in self._variables:
                v.add_handler(self._propagate)
        self._handlers.add(handler)

    def remove_handler(self, handler: Callable[[Constraint], None]) -> None:
        self._handlers.discard(handler)
        if not self._handlers:
            for v in self._variables:
                v.remove_handler(self._propagate)

    def notify(self):
        for handler in self._handlers:
            handler(self)

    def _propagate(self, variable, _old):
        self.mark_dirty(variable)
        self.notify()

    def weakest(self):
        """Return the weakest variable.

        The weakest variable should be always as first element of
        Constraint._weakest list.
        """
        return self._weakest[0][1]

    def mark_dirty(self, var: Variable) -> None:
        """Mark variable dirty and if possible move it to the end of
        Constraint.weakest list to maintain weakest variable invariants (see
        gaphas.solver module documentation)."""

        if isinstance(var, Variable):
            key = (id(var), var)
            try:
                self._weakest.remove(key)
            except ValueError:
                return
            else:
                self._weakest.append(key)
                return

    def solve(self):
        """Solve the constraint.

        This is done by determining the weakest variable and calling
        solve_for() for that variable. The weakest variable is always in
        the set of variables with the weakest strength. The least
        recently changed variable is considered the weakest.
        """
        wvar = self.weakest()
        self.solve_for(wvar)

    def solve_for(self, var):
        """Solve the constraint for a given variable.

        The variable itself is updated.
        """
        raise NotImplementedError


class MultiConstraint:
    """A constraint containing constraints."""

    def __init__(self, *constraints: Constraint):
        self._constraints = constraints

    @property
    def constraints(self) -> Collection[Constraint]:
        return self._constraints

    def add_handler(self, handler: Callable[[Constraint], None]) -> None:
        for c in self._constraints:
            c.add_handler(handler)

    def remove_handler(self, handler: Callable[[Constraint], None]) -> None:
        for c in self._constraints:
            c.remove_handler(handler)

    def solve(self):
        for c in self._constraints:
            c.solve()
