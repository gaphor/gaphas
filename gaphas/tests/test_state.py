import unittest
from builtins import object

import six

from gaphas.state import reversible_pair, observed, _reverse


class SList(object):
    def __init__(self):
        self.l = list()

    def add(self, node, before=None):
        if before:
            self.l.insert(self.l.index(before), node)
        else:
            self.l.append(node)

    add = observed(add)

    @observed
    def remove(self, node):
        self.l.remove(self.l.index(node))


class StateTestCase(unittest.TestCase):
    def test_adding_pair(self):
        """Test adding reversible pair
        """
        reversible_pair(
            SList.add,
            SList.remove,
            bind1={"before": lambda self, node: self.l[self.l.index(node) + 1]},
        )

        if six.PY2:
            self.assertTrue(SList.add.__func__ in _reverse)
            self.assertTrue(SList.remove.__func__ in _reverse)
        if six.PY3:
            self.assertTrue(SList.add in _reverse)
            self.assertTrue(SList.remove in _reverse)
