"""Item constraint creation tests.

The test check functionality of `Item.constraint` method, not
constraints themselves.
"""

from gaphas.item import Element, Line


class Custom:
    def __init__(self, custom):
        self.custom = custom


def test_can_pass_arbitrary_arguments_to_an_element(connections):
    class Test(Element, Custom):
        pass

    t = Test(connections, custom="custom")

    assert t.custom == "custom"
    assert t._connections is connections


def test_can_pass_arbitrary_arguments_to_a_line(connections):
    class Test(Line, Custom):
        pass

    t = Test(connections, custom="custom")

    assert t.custom == "custom"
    assert t._connections is connections
