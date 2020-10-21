from gaphas.solver import STRONG, solvable


def test_solvable_decorator():
    class A:
        x = solvable(varname="sx", strength=STRONG)

    a = A()

    assert isinstance(A.x, solvable)
    assert a.x == 0
    assert a.x.strength == STRONG


def test_solvable_value():
    class A:
        x = solvable(varname="sx", strength=STRONG)

    a = A()
    a.x = 3

    assert a.x == 3
