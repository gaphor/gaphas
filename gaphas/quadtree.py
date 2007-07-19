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
    The Quad-tree.

    Rectangles use the same scheme throughout Gaphas: (x, y, width, height)

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

    Find all items in the tree::

    >>> qtree.find_inside((0, 0, 100, 100))
    ['11', '12', '0', '1', '2', '3', '4', '9', '10', '13', '18', '19', '5', '6', '7', '8', '14', '15', '16', '17']

    Or just the items in a section of the tree::

    >>> qtree.find_inside((40, 40, 40, 40))
    ['13', '14', '15', '16']
    >>> [qtree.get_bounds(item) for item in qtree.find_inside((40, 40, 40, 40))]
    [(52, 40, 10, 10), (56, 50, 10, 10), (60, 60, 10, 10), (64, 70, 10, 10)]

    >>> qtree.find_intersect((40, 40, 20, 20))
    ['12', '13', '14', '15']
    >>> [qtree.get_bounds(item) for item in qtree.find_intersect((40, 40, 20, 20))]
    [(48, 30, 10, 10), (52, 40, 10, 10), (56, 50, 10, 10), (60, 60, 10, 10)]

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
        assert contains(bounds, self._bucket._bounds)
        if item in self._ids:
            _, bucket = self._ids[item]
            if contains(bounds, bucket._bounds):
                # Already placed in right bucket, update bounds and quit
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
        return self._ids[item][0]

    def find_inside(self, rect):
        """
        Find all items in the given rectangle (x, y, with, height).
        Returns an iterator.
        """
        return list(self._bucket.find(rect, method=contains))
        
    def find_intersect(self, rect):
        """
        Find all items that intersect with the given rectangle
        (x, y, width, height).
        Returns an iterator.
        """
        return list(self._bucket.find(rect, method=intersects))
        
    def __len__(self):
        return len(self._ids)

    def dump(self):
        """
        Print structure to stdout.
        """
        self._bucket.dump()


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
        if not self._buckets and len(self._items) >= QuadtreeBucket.CAPACITY:
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
                if contains(bounds, bucket._bounds):
                    return bucket.add(item, bounds)
            else:
                self._items.append((item, bounds))
        return self

    def remove(self, item):
        """
        Remove an item from the quadtree bucket.
        """

    def find(self, rect, method):
        """
        Find all items in the given rectangle (x, y, with, height).
        Method can be either the contains or intersects function.

        Returns an iterator.
        """
        if intersects(rect, self._bounds):
            rx, ry, rw, rh = rect
            for item, bounds in self._items:
                bx, by, bw, bh = bounds
                if method(bounds, rect):
                    yield item
            for bucket in self._buckets or []:
                for item in bucket.find(rect, method=method):
                    yield item
                
    def clear(self):
        """
        Clear the bucket, including sub-buckets.
        """
        self._buckets = None
        del self._items[:]

    def dump(self, indent=''):
       print indent, self, self._bounds
       indent += '  '
       for item, bounds in self._items:
           print indent, item, bounds
       for bucket in self._buckets or []:
           bucket.dump(indent)


def contains(inner, outer):
    """
    Returns True if inner rect is contained in outer rect.
    """
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih


def intersects(recta, rectb):
    """
    Return True if recta and rectb intersect.

    >>> intersects((5,5,20, 20), (10, 10, 1, 1))
    True
    >>> intersects((40, 30, 10, 1), (1, 1, 1, 1))
    False
    """
    ax, ay, aw, ah = recta
    bx, by, bw, bh = rectb
    return ax <= bx + bw and ax + aw >= bx and ay <= by + bh and ay + ah >= by


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
