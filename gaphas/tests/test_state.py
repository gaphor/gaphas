import sys
import unittest
from builtins import object

from gaphas.state import reversible_pair, observed, _reverse


class SList(object):
    def __init__(self):
        self.list = list()

    def add(self, node, before=None):
        if before:
            self.list.insert(self.list.index(before), node)
        else:
            self.list.append(node)

    add = observed(add)

    @observed
    def remove(self, node):
        self.list.remove(self.list.index(node))


class StateTestCase(unittest.TestCase):
    def test_adding_pair(self):
        """Test adding reversible pair
        """
        reversible_pair(
            SList.add,
            SList.remove,
            bind1={"before": lambda self, node: self.list[self.list.index(node) + 1]},
        )

        if sys.version_info.major >= 3:  # Modern Python
            self.assertTrue(SList.add in _reverse)
            self.assertTrue(SList.remove in _reverse)
        else:  # Legacy Python
            self.assertTrue(SList.add.__func__ in _reverse)
            self.assertTrue(SList.remove.__func__ in _reverse)
