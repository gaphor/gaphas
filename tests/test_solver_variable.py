from gaphas.solver import STRONG, Variable, variable


def test_variable_decorator():
    """
    Decorator that variable variable.

    Args:
    """
    class A:
        x = variable(varname="sx", strength=STRONG)

    a = A()

    assert isinstance(A.x, variable)
    assert a.x == 0
    assert a.x.strength == STRONG


def test_variable_decorator_value():
    """
    Decorator that adds a variable to the test variable.

    Args:
    """
    class A:
        x = variable(varname="sx", strength=STRONG)

    a = A()
    a.x = 3

    assert a.x == 3


def test_equality():
    """
    Evaluate the test variable.

    Args:
    """
    v = Variable(3)
    w = Variable(3)
    o = Variable(2)

    assert v == 3
    assert 3 == v
    assert v == w
    assert not v == o

    assert v != 2
    assert 2 != v
    assert not 3 != v
    assert v != o


def test_add_to_variable():
    """
    Adds a variable to the variable.

    Args:
    """
    v = Variable(3)

    assert v + 1 == 4
    assert v - 1 == 2
    assert 1 + v == 4
    assert 4 - v == 1


def test_add_to_variable_with_variable():
    """
    Add variable to variable.

    Args:
    """
    v = Variable(3)
    o = Variable(1)

    assert v + o == 4
    assert v - o == 2


def test_mutiplication():
    """
    Deter implementation of the cross - quaternion.

    Args:
    """
    v = Variable(3)

    assert v * 2 == 6
    assert v / 2 == 1.5
    assert v // 2 == 1

    assert 2 * v == 6
    assert 4.5 / v == 1.5
    assert 4 // v == 1


def test_mutiplication_with_variable():
    """
    Evaluate a variable variable variable ising test.

    Args:
    """
    v = Variable(3)
    o = Variable(2)

    assert v * o == 6
    assert v / o == 1.5
    assert v // o == 1


def test_comparison():
    """
    Check if two variables existance

    Args:
    """
    v = Variable(3)

    assert v > 2
    assert v < 4
    assert v >= 2
    assert v >= 3
    assert v <= 4
    assert v <= 3

    assert not v > 3
    assert not v < 3
    assert not v <= 2
    assert not v >= 4


def test_inverse_comparison():
    """
    Checks if a variable exists in the current context

    Args:
    """
    v = Variable(3)

    assert 4 > v
    assert 2 < v
    assert 4 >= v
    assert 3 >= v
    assert 2 <= v
    assert 3 <= v

    assert not 3 > v
    assert not 3 < v
    assert not 4 <= v
    assert not 2 >= v


def test_power():
    """
    Evaluate the power of a given power.

    Args:
    """
    v = Variable(3)
    o = Variable(2)

    assert v ** 2 == 9
    assert 2 ** v == 8
    assert v ** o == 9


def test_modulo():
    """
    Compute modulo modulo modulo modulo modulo modulus.

    Args:
    """
    v = Variable(3)
    o = Variable(2)

    assert v % 2 == 1
    assert 4 % v == 1
    assert v % o == 1
    assert divmod(v, 2) == (1, 1)
    assert divmod(4, v) == (1, 1)
    assert divmod(v, o) == (1, 1)
