"""Item constraint creation tests.

The test check functionality of `Item.constraint` method, not
constraints themselves.
"""

from gaphas.item import Element, Line


class Custom:
    def __init__(self, custom):
        """
        Initializes the custom custom settings.

        Args:
            self: (todo): write your description
            custom: (todo): write your description
        """
        self.custom = custom


def test_can_pass_arbitrary_arguments_to_an_element(connections):
    """
    Tests if a callback can be called when a callback.

    Args:
        connections: (todo): write your description
    """
    class Test(Element, Custom):
        pass

    t = Test(connections, custom="custom")

    assert t.custom == "custom"
    assert t._connections is connections


def test_can_pass_arbitrary_arguments_to_a_line(connections):
    """
    Determine if the line can be used in a line.

    Args:
        connections: (todo): write your description
    """
    class Test(Line, Custom):
        pass

    t = Test(connections, custom="custom")

    assert t.custom == "custom"
    assert t._connections is connections
