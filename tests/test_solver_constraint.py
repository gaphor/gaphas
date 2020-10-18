from gaphas.solver import Constraint, Projection, Variable


def test_constraint_propagates_variable_changed():
    v = Variable()
    c = Constraint(v)
    events = []

    def handler(c):
        events.append(c)

    c.add_handler(handler)

    v.value = 3

    assert events == [c]


def test_constraint_propagates_variable_wrapped_in_projection():
    v = Variable()
    p = Projection(v)
    c = Constraint(p)
    events = []

    def handler(c):
        events.append(c)

    c.add_handler(handler)

    v.value = 3

    assert events == [c]
