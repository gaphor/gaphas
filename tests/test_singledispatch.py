import pytest

from gaphas.aspect import singledispatch


class Custom:
    pass


class Another:
    pass


@singledispatch
def f(o):
    return object, o


@f.register(str)
def _str_dispatcher(s):
    return str, s


@f.when_type(int)
def _int_dispatcher(i):
    return int, i


@f.when_type(Custom, float)
def _bool_float_dispatcher(i):
    return Custom, i


def test_singledispatch_with_registered_function():
    assert (str, "abc") == f("abc")


def test_singledispatch_with_when_type_function():
    assert (int, 3) == f(3)


def test_singledispatch_with_when_type_function_and_multiple_types():
    custom = Custom()
    assert (Custom, 3.0) == f(3.0)
    assert (Custom, custom) == f(custom)


def test_singledispatch_with_when_type_and_no_types():
    with pytest.raises(TypeError):

        @f.when_type()
        def errorous():
            pass
