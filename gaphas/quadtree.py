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

import operator


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
         10 (40, 10, 10, 10)
         2 (8, 20, 10, 10)
         3 (12, 30, 10, 10)
         4 (16, 40, 10, 10)
         9 (36, 0, 10, 10)
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

    >>> sorted(qtree.find_inside((0, 0, 100, 100)))
    ['0', '1', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2', '3', '4', '5', '6', '7', '8', '9']

    Or just the items in a section of the tree::

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
        self._capacity = capacity
        self._bucket = QuadtreeBucket(bounds, capacity)

        # Easy lookup item->(bounds, data, clipped bounds) mapping
        self._ids = dict()

    def resize(self, bounds):
        self._bucket = QuadtreeBucket(bounds, self._capacity)
        self.rebuild()

    bounds = property(lambda s: s._bucket.bounds)

    def get_soft_bounds(self):
        """
        Calculate the size of all items in the Quadtree. This size may be beyond
        the limits of the quadtree itself 
        >>> qtree = Quadtree()
        >>> qtree.add('1', (10, 20, 30, 40))
        >>> qtree.add('2', (20, 30, 40, 10))
        >>> qtree.bounds
        (0, 0, 0, 0)
        >>> qtree.autosize()
        (10, 20, 50, 40)

        Quadtree's bounding box is not adjusted:

        >>> qtree.bounds
        (0, 0, 0, 0)
        """
        x_y_w_h = zip(*map(operator.getitem, self._ids.itervalues(), [0] * len(self._ids)))
        x0 = min(x_y_w_h[0])
        y0 = min(x_y_w_h[1])
        add = operator.add
        x1 = max(map(add, x_y_w_h[0], x_y_w_h[2]))
        y1 = max(map(add, x_y_w_h[1], x_y_w_h[3]))
        return (x0, y0, x1 - x0, y1 - y0)

    soft_bounds = property(get_soft_bounds)

    def add(self, item, bounds, data=None, debug=False):
        """
        Add an item to the tree.
        If an item already exists, its bounds are updated and the item is
        moved to the right bucket.
        Data can be used to add some extra info to the item
        """
        # Clip item bounds to fit in top-level bucket
        # Keep original bounds in _ids, for reference
        clipped_bounds = clip(bounds, self._bucket.bounds)

        if item in self._ids:
            old_clip = self._ids[item][2]
            bucket = old_clip and self._bucket.find_bucket(old_clip)
            assert not bucket or item in bucket.items
            if bucket and contains(bounds, bucket.bounds):
                bucket.update(item, old_clip, clipped_bounds)
                self._ids[item] = (bounds, data, clipped_bounds)
                return
            elif bucket:
                bucket.remove(item, old_clip)

        if clipped_bounds:
            self._bucket.add(item, clipped_bounds)
        self._ids[item] = (bounds, data, clipped_bounds)

    def remove(self, item):
        """
        Remove an item from the tree
        """
        bounds, data, clip = self._ids[item]
        del self._ids[item]
        bucket = self._bucket.find_bucket(clip)
        bucket.remove(item, bounds)

    def rebuild(self):
        """
        Rebuild the Quadtree structure.
        """
        # Clean bucket and items:
        self._bucket.clear()

        for item, (bounds, data, _) in dict(self._ids).iteritems():
            clipped_bounds = clip(bounds, self._bucket.bounds)
            if clipped_bounds:
                self._bucket.add(item, clipped_bounds)
            self._ids[item] = (bounds, data, clipped_bounds)

    def get_bounds(self, item):
        """
        Return the bounding box for the given item.
        """
        return self._ids[item][0]

    def get_data(self, item):
        return self._ids[item][1]

    def get_clipped_bounds(self, item):
        return self._ids[item][2]

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

    def __init__(self, bounds, capacity):
        """
        Set bounding box for the node as (x, y, width, height).
        """
        self.bounds = bounds
        self.capacity = capacity

        self.items = {}
        self._buckets = []

    buckets = property(lambda s: s._buckets)

    def add(self, item, bounds):
        """
        Add an item to the quadtree.
        """
        # create new subnodes if threshold is reached
        if not self._buckets and len(self.items) >= self.capacity:
            x, y, w, h = self.bounds
            rw, rh = w / 2., h / 2.
            cx, cy = x + rw, y + rh
            self._buckets = [QuadtreeBucket((x, y, rw, rh), self.capacity),
                             QuadtreeBucket((cx, y, rw, rh), self.capacity),
                             QuadtreeBucket((x, cy, rw, rh), self.capacity),
                             QuadtreeBucket((cx, cy, rw, rh), self.capacity)]
            # Add items to subnodes
            items = self.items.items()
            self.items.clear()
            for i in items:
                self.add(*i)
        if not self._buckets:
            self.items[item] = bounds
        else:
            bucket = self.find_bucket(bounds)
            if bucket is self:
                self.items[item] = bounds
            else:
                bucket.add(item, bounds)

    def update(self, item, old_bounds, new_bounds):
        self.remove(item, old_bounds)
        self.add(item, new_bounds)

    def remove(self, item, bounds):
        """
        Remove an item from the quadtree bucket.
        Returns True if the item was found in this bucket or one of it's
        sub-buckets.
        """
        if item in self.items:
            del self.items[item]
            return True
        else:
            bucket = self.find_bucket(bounds)
            bucket.remove(item, bounds)
        
    def find_bucket(self, bounds):
        """
        Find the bucket that holds a bounding box.
        """
        if self._buckets:
            sx, sy, sw, sh = self.bounds
            cx, cy = sx + sw / 2., sy + sh / 2.
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
        if intersects(rect, self.bounds):
            rx, ry, rw, rh = rect
            for item, bounds in self.items.iteritems():
                bx, by, bw, bh = bounds
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

    def dump(self, indent=''):
       print indent, self, self.bounds
       indent += '  '
       for item, bounds in sorted(self.items.iteritems()):
           print indent, item, bounds
       for bucket in self._buckets:
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

def clip(recta, rectb):
    """
    Return the clipped rectangle of recta and rectb. If they do not intersect,
    None is returned.
    >>> clip((0, 0, 20, 20), (10, 10, 20, 20))
    (10, 10, 10, 10)
    """
    ax, ay, aw, ah = recta
    bx, by, bw, bh = rectb
    x = max(ax, bx)
    y = max(ay, by)
    w = min(ax +aw, bx + bw) - x
    h = min(ay +ah, by + bh) - y
    if w < 0 or h < 0:
        return None
    return (x, y, w, h)
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et:ai
