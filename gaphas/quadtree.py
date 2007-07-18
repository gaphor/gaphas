"""
Quadtree
========
From Wikipedia, the free encyclopedia

A quadtree is a tree data structure in which each internal node has up to four
children. Quadtrees are most often used to partition a two dimensional space by
recursively subdividing it into four quadrants or regions. The regions may be
square or rectangular, or may have arbitrary shapes. This data structure was
named a quadtree by Raphael Finkel and J.L. Bentley in 1974. A similar
partitioning is also known as a Q-tree. All forms of Quadtrees share some
common features:

* They decompose space into adaptable cells
* Each cell (or bucket) has a maximum capacity.
  When maximum capacity is reached, the bucket splits
* The tree directory follows the spatial decomposition of the Quadtree

"""


class Quadtree(object):
    """
    The Quad-tree. Rectangles use the same scheme throughout Gaphas:
    (x, y, width, height)

    >>> qtree = Quadtree((0, 0, 100, 100))
    >>> qtree.add('a', (20, 10, 10, 10))
    >>> qtree._bucket._items
    [('a', (20, 10, 10, 10))]
    >>> qtree._bucket.buckets
    >>> for i in range(20):
    ...     qtree.add(i, ((i * 4) % 90, (i * 10) % 90, 10, 10))
    >>> qtree._bucket._items
    [(11, (44, 20, 10, 10)), (12, (48, 30, 10, 10))]
    >>> len(qtree._ids)
    21
    >>> qtree.find_inside((0, 0, 100, 100))
    [11, 12, 'a', 0, 1, 2, 3, 4, 9, 10, 13, 18, 19, 5, 6, 7, 8, 14, 15, 16, 17]
    """

    def __init__(self, bounds):
        # TODO: extend bounds to a specific factor (e.g. 100 or 1000)
        self._bucket = QuadtreeBucket(bounds)
        # Easy lookup item->(bounds, bucket) mapping
        self._ids = dict()

    def add(self, item, bounds):
        """
        Add an item to the tree.
        If an item already exists, its bounds are updated and the item is
        moved to the right bucket.
        """
        assert bounds in self._bucket
        try:
            bounds, bucket = self._ids[item]
        except KeyError:
            # New entry
            pass
        else:
            if bounds in bucket:
                # Already placed in right bucket
                self._ids[item] = (bounds, bucket)
                return
            else:
                bucket.remove(item)
        bucket = self._bucket.add(item, bounds)
        self._ids[item] = (bounds, bucket)

    def remove(self, item):
        """
        Remove an item from the tree
        """
        bounds, bucket = self._ids[item]
        del self._ids[item]
        bucket.remove(item)

    def rebuild(self):
        """
        Rebuild the Quadtree structure.
        """
        # Clean bucket and items:
        self._bucket.clear()

        # Now add each item using the bounds tree:
        add = self._bucket.add
        for item, (bounds, bucket) in self._ids:
            add(item, bounds)

    def get_bounds(self, item):
        """
        Return the bounding box for the given item.
        """
        return self._ids[item][1]

    def find_inside(self, rect):
        return list(self._bucket.find_inside(rect))
        
    def find_intersect(self, rect):
        return list(self._bucket.find_intersect(rect))
        

class QuadtreeBucket(object):
    """
    A node in a Quadtree structure.
    """

    CAPACITY = 10

    def __init__(self, bounds):
        """
        Set bounding box for the node as (x, y, width, height).
        """
        self._bounds = bounds

        self._items = list()
        self._buckets = None

    buckets = property(lambda s: s._buckets)

    def add(self, item, bounds):
        """
        Add an item to the quadtree.
        Return the bucket the item is attached to.
        """
        # create new subnodes if threshold is reached
        if not self._buckets and len(self._items) > QuadtreeBucket.CAPACITY:
            x, y, w, h = self._bounds
            rw, rh = w / 2., h / 2.
            cx, cy = x + rw, y + rh
            self._buckets = [QuadtreeBucket((x, y, rw, rh)),
                             QuadtreeBucket((cx, y, rw, rh)),
                             QuadtreeBucket((x, cy, rw, rh)),
                             QuadtreeBucket((cx, cy, rw, rh))]
            # Add items to subnodes
            items = list(self._items)
            del self._items[:]
            for i in items:
                self.add(*i)
        if not self._buckets:
            self._items.append((item, bounds))
        else:
            for bucket in self._buckets:
                if bounds in bucket:
                    return bucket.add(item, bounds)
            else:
                self._items.append((item, bounds))
        return self

    def remove(self, item):
        """
        Remove an item from the quadtree bucket.
        """

    def find_inside(self, rect):
        """
        Find all items in the given rectangle (x, y, with, height).
        Returns an iterator.
        """
        if 1: #rect in self:
            rx, ry, rw, rh = rect
            for item, bounds in self._items:
                bx, by, bw, bh = bounds
                if rx <= bx and ry <= by and \
                        rx + rw >= bx + bw and ry + rh >= by + bh:
                    yield item
            for bucket in self._buckets or []:
                for item in bucket.find_inside(rect):
                    yield item
                
    def find_intersect(self, rect):
        """
        Find all items that intersect with the given rectangle
        (x, y, width, height).
        Returns an iterator.
        """

    def clear(self):
        """
        Clear the bucket, including sub-buckets.
        """
        self._buckets = None
        del self._items[:]

    def __contains__(self, bounds):
        """
        Check if rectangle bounds (tuple (x, y, width, height)) is located
        *inside* the bucket.
        """
        x, y, w, h = bounds
        bx, by, bw, bh = self._bounds
        return bx <= x and by <= y and bx + bw >= x + w and by + bh >= y + h


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
