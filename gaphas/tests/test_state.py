import unittest

from gaphas.state import reversible_pair, observed, _reverse

class SList(object):
    def __init__(self):
        self.l = list()
    def add(self, node, before=None):
        if before: self.l.insert(self.l.index(before), node)
        else: self.l.append(node)
    add = observed(add)
    @observed
    def remove(self, node):
        self.l.remove(self.l.index(node))

class StateTestCase(unittest.TestCase):
    def test_adding_pair(self):
        """Test adding reversible pair
        """
        reversible_pair(SList.add, SList.remove, \
            bind1={'before': lambda self, node: self.l[self.l.index(node)+1] })

        self.assertTrue(SList.add.im_func in _reverse)
        self.assertTrue(SList.remove.im_func in _reverse)
