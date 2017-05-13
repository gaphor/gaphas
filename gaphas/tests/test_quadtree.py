#!/usr/bin/env python

# Copyright (C) 2007-2009 Arjan Molenaar <gaphor@gmail.com>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.
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

    def test_with_rectangles(self):
        from gaphas.geometry import Rectangle

        qtree = Quadtree((0, 0, 100, 100))
        for i in range(0, 100, 10):
            for j in range(0, 100, 10):
                qtree.add("%dx%d" % (i, j), Rectangle(i, j, 10, 10))
        assert len(qtree._ids) == 100, len(qtree._ids)

        for i in range(100, 10):
            for j in range(100, 10):
                assert qtree.find_intersect((i+1, j+1, 1, 1)) == ['%dx%d' % (i, j)], \
                        qtree.find_intersect((i+1, j+1, 1, 1))


    def test_moving_items(self):
        qtree = Quadtree((0, 0, 100, 100), capacity=10)
        for i in range(0, 100, 10):
            for j in range(0, 100, 10):
                qtree.add("%dx%d" % (i, j), (i, j, 10, 10))
        assert len(qtree._ids) == 100, len(qtree._ids)
        assert qtree._bucket._buckets, qtree._bucket._buckets
        for i in range(4):
            assert qtree._bucket._buckets[i]._buckets
            for j in range(4):
                assert not qtree._bucket._buckets[i]._buckets[j]._buckets

        # Check contents:
        # First sub-level contains 9 items. second level contains 4 items
        # ==> 4 * (9 + (4 * 4)) = 100
        assert len(qtree._bucket.items) == 0, qtree._bucket.items
        for i in range(4):
            assert len(qtree._bucket._buckets[i].items) == 9
            for item, bounds in qtree._bucket._buckets[i].items.iteritems():
                assert qtree._bucket.find_bucket(bounds) is qtree._bucket._buckets[i]
            for j in range(4):
                assert len(qtree._bucket._buckets[i]._buckets[j].items) == 4

        assert qtree.get_bounds('0x0')
        # Now move item '0x0' to the center of the first quadrant (20, 20)
        qtree.add('0x0', (20, 20, 10, 10))
        assert len(qtree._bucket.items) == 0
        assert len(qtree._bucket._buckets[0]._buckets[0].items) == 3, \
                qtree._bucket._buckets[0]._buckets[0].items
        assert len(qtree._bucket._buckets[0].items) == 10, \
                qtree._bucket._buckets[0].items

        # Now move item '0x0' to the second quadrant (70, 20)
        qtree.add('0x0', (70, 20, 10, 10))
        assert len(qtree._bucket.items) == 0
        assert len(qtree._bucket._buckets[0]._buckets[0].items) == 3, \
                qtree._bucket._buckets[0]._buckets[0].items
        assert len(qtree._bucket._buckets[0].items) == 9, \
                qtree._bucket._buckets[0].items
        assert len(qtree._bucket._buckets[1].items) == 10, \
                qtree._bucket._buckets[1].items


    def test_get_data(self):
        """
        Extra data may be added to a node:
        """
        qtree = Quadtree((0, 0, 100, 100))
        for i in range(0, 100, 10):
            for j in range(0, 100, 10):
                qtree.add("%dx%d" % (i, j), (i, j, 10, 10), i+j)

        for i in range(0, 100, 10):
            for j in range(0, 100, 10):
                assert i+j == qtree.get_data("%dx%d" % (i, j))

    def test_clipped_bounds(self):
        qtree = Quadtree((0, 0, 100, 100), capacity=10)
        qtree.add(1, (-100, -100, 120, 120))
        self.assertEquals((0, 0, 20, 20), qtree.get_clipped_bounds(1))


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
