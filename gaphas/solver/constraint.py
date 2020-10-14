from typing import Union

from gaphas.solver.projection import Projection
from gaphas.solver.variable import Variable


class Constraint:
    """Constraint base class.

    - variables - list of all variables
    - weakest   - list of weakest variables
    """

    disabled = False

    def __init__(self, *variables):
        """Create new constraint, register all variables, and find weakest
        variables.

        Any value can be added. It is assumed to be a variable if it has
        a 'strength' attribute.
        """
        self._variables = [v for v in variables if hasattr(v, "strength")]
        self._weakest = []
        self._handlers = set()

        self.create_weakest_list()

        # Used by the Solver for efficiency
        self._solver_has_projections = False

    def variables(self):
        """Return an iterator which iterates over the variables that are held
        by this constraint."""
        return self._variables

    def add_handler(self, handler):
        if not self._handlers:
            for v in self._variables:
                v.add_handler(self._propagate)
        self._handlers.add(handler)

    def remove_handler(self, handler):
        self._handlers.discard(handler)
        if not self._handlers:
            for v in self._variables:
                v.remove_handler(self._propagate)

    def notify(self):
        for handler in self._handlers:
            handler(self)

    def _propagate(self, variable):
        self.mark_dirty(variable)
        self.notify()

    def create_weakest_list(self):
        """Create list of weakest variables."""
        strength = min(v.strength for v in self._variables)
        self._weakest = [v for v in self._variables if v.strength == strength]

    def weakest(self):
        """Return the weakest variable.

        The weakest variable should be always as first element of
        Constraint._weakest list.
        """
        return self._weakest[0]

    def mark_dirty(self, var: Union[Projection, Variable]):
        """Mark variable v dirty and if possible move it to the end of
        Constraint.weakest list to maintain weakest variable invariants (see
        gaphas.solver module documentation)."""
        weakest = self.weakest()
        # Fast lane:
        if var is weakest:
            self._weakest.remove(var)
            self._weakest.append(var)
            return

        # Handle projected variables well:
        global Projection
        p = weakest
        while isinstance(weakest, Projection):
            weakest = weakest.variable()
            if var is weakest:
                self._weakest.remove(p)
                self._weakest.append(p)
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
