
import unittest
from gaphas.quadtree import Quadtree

class QuadtreeTestCase(unittest.TestCase):

    def test_lookups(self):
        qtree = Quadtree((0, 0, 100, 100))
        for i in range(100, 10):
            for j in range(100, 10):
                qtree.add("%dx%d" % (i, j), (i, j, 10, 10))

        for i in range(100, 10):
            for j in range(100, 10):
                assert qtree.find_intersect((i+1, j+1, 1, 1)) == ['%dx%d' % (i, j)], \
                        qtree.find_intersect((i+1, j+1, 1, 1))


