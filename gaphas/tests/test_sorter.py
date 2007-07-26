import unittest

from gaphas.sorter import Sorted
from gaphas.canvas import Canvas
from gaphas.item import Element

class SortedTestCase(unittest.TestCase):
    def test_discard(self):
        """Test removal of an item from Sorted collection"""
        e1 = Element()
        e2 = Element()

        c = Canvas()
        c.add(e1)
        c.add(e2)

        items = Sorted(c)
        items.add(e1)
        items.add(e2)

        assert e1 in items and e2 in items

        items.discard(e1)
        items.discard(e1) # silent discard
        self.assertTrue(e1 not in items)

        items.discard(e2)
        self.assertTrue(e2 not in items)
