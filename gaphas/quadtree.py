"""
Quadtree
========

A quadtree is a tree data structure in which each internal node has up
to four children. Quadtrees are most often used to partition a two
dimensional space by recursively subdividing it into four quadrants or
regions. The regions may be square or rectangular, or may have
arbitrary shapes. This data structure was named a quadtree by Raphael
Finkel and J.L. Bentley in 1974. A similar partitioning is also known
as a Q-tree. All forms of Quadtrees share some common features:

* They decompose space into adaptable cells.
* Each cell (or bucket) has a maximum capacity.
  When maximum capacity is reached, the bucket splits.
* The tree directory follows the spatial decomposition of the Quadtree.

(From Wikipedia, the free encyclopedia)
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import operator
from builtins import map
from builtins import object
from builtins import zip

from .geometry import rectangle_contains, rectangle_intersects, rectangle_clip


class Quadtree(object):
    """
    The Quad-tree.

    Rectangles use the same scheme throughout Gaphas: (x, y, width, height).

    >>> qtree = Quadtree((0, 0, 100, 100))
    >>> for i in range(20):
    ...     qtree.add('%d' % i, ((i * 4) % 90, (i * 10) % 90, 10, 10))
    >>> len(qtree)
    20
    >>> qtree.dump() # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
     <....QuadtreeBucket object at 0x...> (0, 0, 100, 100)
       11 (44, 20, 10, 10)
       12 (48, 30, 10, 10)
       <....QuadtreeBucket object at 0x...> (0, 0, 50.0, 50.0)
         0 (0, 0, 10, 10)
         1 (4, 10, 10, 10)
         2 (8, 20, 10, 10)
         3 (12, 30, 10, 10)
         4 (16, 40, 10, 10)
         9 (36, 0, 10, 10)
         10 (40, 10, 10, 10)
       <....QuadtreeBucket object at 0x...> (50.0, 0, 50.0, 50.0)
         13 (52, 40, 10, 10)
         18 (72, 0, 10, 10)
         19 (76, 10, 10, 10)
       <....QuadtreeBucket object at 0x...> (0, 50.0, 50.0, 50.0)
         5 (20, 50, 10, 10)
         6 (24, 60, 10, 10)
         7 (28, 70, 10, 10)
         8 (32, 80, 10, 10)
       <....QuadtreeBucket object at 0x...> (50.0, 50.0, 50.0, 50.0)
         14 (56, 50, 10, 10)
         15 (60, 60, 10, 10)
         16 (64, 70, 10, 10)
         17 (68, 80, 10, 10)

    Find all items in the tree:

    >>> sorted(qtree.find_inside((0, 0, 100, 100)))
    ['0', '1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2', '3', '4', '5', '6', '7', '8', '9']

    Or just the items in a section of the tree:

    >>> sorted(qtree.find_inside((40, 40, 40, 40)))
    ['13', '14', '15', '16']
    >>> sorted([qtree.get_bounds(item) for item in qtree.find_inside((40, 40, 40, 40))])
    [(52, 40, 10, 10), (56, 50, 10, 10), (60, 60, 10, 10), (64, 70, 10, 10)]

    >>> sorted(qtree.find_intersect((40, 40, 20, 20)))
    ['12', '13', '14', '15']
    >>> sorted([qtree.get_bounds(item) for item in qtree.find_intersect((40, 40, 20, 20))])
    [(48, 30, 10, 10), (52, 40, 10, 10), (56, 50, 10, 10), (60, 60, 10, 10)]
    >>> qtree.rebuild()
    """

    def __init__(self, bounds=(0, 0, 0, 0), capacity=10):
        """
        Create a new Quadtree instance.

        Bounds is the boundries of the quadtree. this is fixed and do not
        change depending on the contents.

        Capacity defines the number of elements in one tree bucket (default: 10)
        """
        self._capacity = capacity
        self._bucket = QuadtreeBucket(bounds, capacity)

        # Easy lookup item->(bounds, data, clipped bounds) mapping
        self._ids = dict()

    bounds = property(lambda s: s._bucket.bounds)

    def resize(self, bounds):
        """
        Resize the tree.
        The tree structure is rebuild.
        """
        self._bucket = QuadtreeBucket(bounds, self._capacity)
        self.rebuild()

    def get_soft_bounds(self):
        """
        Calculate the size of all items in the tree. This size may be
        beyond the limits of the tree itself.

        Returns a tuple (x, y, width, height).

        >>> qtree = Quadtree()
        >>> qtree.add('1', (10, 20, 30, 40))
        >>> qtree.add('2', (20, 30, 40, 10))
        >>> qtree.bounds
        (0, 0, 0, 0)
        >>> qtree.soft_bounds
        (10, 20, 50, 40)

        Quadtree's bounding box is not adjusted:

        >>> qtree.bounds
        (0, 0, 0, 0)
        """
        x_y_w_h = list(
            zip(
                *list(
                    map(
                        operator.getitem,
                        iter(list(self._ids.values())),
                        [0] * len(self._ids),
                    )
                )
            )
        )
        if not x_y_w_h:
            return 0, 0, 0, 0
        x0 = min(x_y_w_h[0])
        y0 = min(x_y_w_h[1])
        add = operator.add
        x1 = max(list(map(add, x_y_w_h[0], x_y_w_h[2])))
        y1 = max(list(map(add, x_y_w_h[1], x_y_w_h[3])))
        return (x0, y0, x1 - x0, y1 - y0)

    soft_bounds = property(get_soft_bounds)

    def add(self, item, bounds, data=None):
        """
        Add an item to the tree.
        If an item already exists, its bounds are updated and the item
        is moved to the right bucket.
        Data can be used to add some extra info to the item
        """
        # Clip item bounds to fit in top-level bucket
        # Keep original bounds in _ids, for reference
        clipped_bounds = rectangle_clip(bounds, self._bucket.bounds)

        if item in self._ids:
            old_clip = self._ids[item][2]
            if old_clip:
                bucket = self._bucket.find_bucket(old_clip)
                assert item in bucket.items
                # Fast lane, if item moved just a little it may still reside
                # in the same bucket. We do not need to search from top-level.
                if (
                    bucket
                    and clipped_bounds
                    and rectangle_contains(clipped_bounds, bucket.bounds)
                ):
                    bucket.update(item, clipped_bounds)
                    self._ids[item] = (bounds, data, clipped_bounds)
                    return
                elif bucket:
                    bucket.remove(item)

        if clipped_bounds:
            self._bucket.find_bucket(clipped_bounds).add(item, clipped_bounds)
        self._ids[item] = (bounds, data, clipped_bounds)

    def remove(self, item):
        """
        Remove an item from the tree.
        """
        bounds, data, clipped_bounds = self._ids[item]
        del self._ids[item]
        if clipped_bounds:
            self._bucket.find_bucket(clipped_bounds).remove(item)

    def clear(self):
        """
        Remove all items from the tree.
        """
        self._bucket.clear()
        self._ids.clear()

    def rebuild(self):
        """
        Rebuild the tree structure.
        """
        # Clean bucket and items:
        self._bucket.clear()

        for item, (bounds, data, _) in list(dict(self._ids).items()):
            clipped_bounds = rectangle_clip(bounds, self._bucket.bounds)
            if clipped_bounds:
                self._bucket.find_bucket(clipped_bounds).add(item, clipped_bounds)
            self._ids[item] = (bounds, data, clipped_bounds)

    def get_bounds(self, item):
        """
        Return the bounding box for the given item.
        """
        return self._ids[item][0]

    def get_data(self, item):
        """
        Return the data for the given item, None if no data was provided.
        """
        return self._ids[item][1]

    def get_clipped_bounds(self, item):
        """
        Return the bounding box for the given item. The bounding box
        is clipped on the boundries of the tree (provided on
        construction or with resize()).
        """
        return self._ids[item][2]

    def find_inside(self, rect):
        """
        Find all items in the given rectangle (x, y, with, height).
        Returns a set.
        """
        return set(self._bucket.find(rect, method=rectangle_contains))

    def find_intersect(self, rect):
        """
        Find all items that intersect with the given rectangle
        (x, y, width, height).
        Returns a set.
        """
        return set(self._bucket.find(rect, method=rectangle_intersects))

    def __len__(self):
        """
        Return number of items in tree.
        """
        return len(self._ids)

    def __contains__(self, item):
        """
        Check if an item is in tree.
        """
        return item in self._ids

    def dump(self):
        """
        Print structure to stdout.
        """
        self._bucket.dump()


class QuadtreeBucket(object):
    """
    A node in a Quadtree structure.
    """

    def __init__(self, bounds, capacity):
        """
        Set bounding box for the node as (x, y, width, height).
        """
        self.bounds = bounds
        self.capacity = capacity

        self.items = {}
        self._buckets = []

    def add(self, item, bounds):
        """
        Add an item to the quadtree.
        The bucket is split when nessecary.
        Items are otherwise added to this bucket, not some sub-bucket.
        """
        assert rectangle_contains(bounds, self.bounds)
        # create new subnodes if threshold is reached
        if not self._buckets and len(self.items) >= self.capacity:
            x, y, w, h = self.bounds
            rw, rh = w / 2.0, h / 2.0
            cx, cy = x + rw, y + rh
            self._buckets = [
                QuadtreeBucket((x, y, rw, rh), self.capacity),
                QuadtreeBucket((cx, y, rw, rh), self.capacity),
                QuadtreeBucket((x, cy, rw, rh), self.capacity),
                QuadtreeBucket((cx, cy, rw, rh), self.capacity),
            ]
            # Add items to subnodes
            items = list(self.items.items())
            self.items.clear()
            for i, b in items:
                self.find_bucket(b).add(i, b)
            self.find_bucket(bounds).add(item, bounds)
        else:
            self.items[item] = bounds

    def remove(self, item):
        """
        Remove an item from the quadtree bucket.
        The item should be contained by *this* bucket (not a sub-bucket).
        """
        del self.items[item]

    def update(self, item, new_bounds):
        """
        Update the position of an item within the current bucket.
        The item should live in the current bucket, but may be placed in a
        sub-bucket.
        """
        assert item in self.items
        self.remove(item)
        self.find_bucket(new_bounds).add(item, new_bounds)

    def find_bucket(self, bounds):
        """
        Find the bucket that holds a bounding box.

        This method should be used to find a bucket that fits, before
        add() or remove() is called.
        """
        if self._buckets:
            sx, sy, sw, sh = self.bounds
            cx, cy = sx + sw / 2.0, sy + sh / 2.0
            x, y, w, h = bounds
            index = 0
            if x >= cx:
                index += 1
            elif x + w > cx:
                return self

            if y >= cy:
                index += 2
            elif y + h > cy:
                return self
            return self._buckets[index].find_bucket(bounds)
        return self

    def find(self, rect, method):
        """
        Find all items in the given rectangle (x, y, with, height).
        Method can be either the contains or intersects function.

        Returns an iterator.
        """
        if rectangle_intersects(rect, self.bounds):
            for item, bounds in list(self.items.items()):
                if method(bounds, rect):
                    yield item
            for bucket in self._buckets:
                for item in bucket.find(rect, method=method):
                    yield item

    def clear(self):
        """
        Clear the bucket, including sub-buckets.
        """
        del self._buckets[:]
        self.items.clear()

    def dump(self, indent=""):
        print(indent, self, self.bounds)
        indent += "   "
        for item, bounds in sorted(self.items.items(), key=lambda items: items[1]):
            print(indent, item, bounds)
        for bucket in self._buckets:
            bucket.dump(indent)


# vim:sw=4:et:ai
