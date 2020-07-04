import sys

from gaphas.state import reversible_pair, observed, _reverse


class SList:
    def __init__(self):
        self.list = []

    def add(self, node, before=None):
        if before:
            self.list.insert(self.list.index(before), node)
        else:
            self.list.append(node)

    add = observed(add)

    @observed
    def remove(self, node):
        self.list.remove(self.list.index(node))


def test_adding_pair():
    """Test adding reversible pair.

    """
    reversible_pair(
        SList.add,
        SList.remove,
        bind1={"before": lambda self, node: self.list[self.list.index(node) + 1]},
    )

    if sys.version_info.major >= 3:  # Modern Python
        assert SList.add in _reverse
        assert SList.remove in _reverse
    else:  # Legacy Python
        assert SList.add.__func__ in _reverse
        assert SList.remove.__func__ in _reverse
