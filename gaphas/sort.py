"""
Sorting algorithms and collections for view and canvas.
"""

__version__ = "$Revision$"
# $HeadURL$

from bisect import insort, bisect
import operator

class Sorter(object):
    """
    Item sorter.

    Attributes:
     - _key: last value of sort key
     - _key_getter: key getter used to extract sort key from item
     - tree: the tree that determines the order of the nodes.
    """

    DELTA = 0.4

    def __init__(self, tree):
        """
        Create item sorter.

        Parameters:
         - canvas: canvas reference
        """
        super(Sorter, self).__init__()

        self._tree = tree

        self._key_getter = operator.attrgetter('_sort_key')
        self._key = 0


    def sort(self, items, reverse=False):
        """
        Sort items.
        
        Items are sorted using standard O(k * log(k)) algorithm but if amount
        of items to be sorted is bigger than::
        
            Sorter._tree._nodes * DELTA

        then O(n) algorithm is used, where
        - k: len(items)
        - n: len(canvas.get_all_items())

        Therefore it is really important, that passed items collection is a set.

        Parameters:
         - items: set of items to be sorted
         - reverse: if True then sort in reverse order
        """
        if len(self._tree._nodes) * self.DELTA > len(items):
            assert isinstance(items, set), 'use set to sort items!'
            if reverse:
                return [item for item in reversed(self._tree._nodes) if item in items]
            else:
                return [item for item in self._tree._nodes if item in items]
        else:
            return sorted(items, key=self._key_getter, reverse=reverse)


    def get_key(self, item):
        """
        Get sorting key for an item.
        """
        self._key += 1

        parent = self._tree.get_parent(item)
        if parent is None:
            key = (self._key, )
        else:
            key = self._key_getter(parent) + (self._key, )

        return key



class Sorted(object):
    """
    Collection of items kept in order defined by canvas. Add/remove
    operations are O(k * log(k)). Checking if an item is in collection
    takes O(1).

    Attributes:
     - _list: sorted list of items
     - _set: set of items
     - _key_getter: key getter used to extract sort key from item
    """
    def __init__(self, canvas = None):
        """
        Create new sorted collection.

        Parameters:
         - canvas: canvas reference
        """
        self._list = []
        self._set = set()
        self._key_getter = None
        self._set_canvas(canvas)


    def _set_canvas(self, canvas):
        """
        Extract key getter from canvas.
        """
        if canvas:
            self._key_getter = canvas.sorter._key_getter
        else:
            self._key_getter = None

    canvas = property(fset=_set_canvas)

    def add(self, item):
        """
        Add an item to collection.
        """
        insort(self._list, (self._key_getter(item), item))
        self._set.add(item)


    def discard(self, item):
        """
        Remove an item from collection.
        """
        if item in self._set:
            i = bisect(self._list, (self._key_getter(item), item)) 
            del self._list[i - 1]
            self._set.discard(item)


    def clear(self):
        """
        Remove all items from collection.
        """
        del self._list[:]
        self._set.clear()


    def difference_update(self, items):
        """
        Remove all items of another sorted collection.
        """
        self._set.difference_update(items)
        for item in items:
            i = bisect(self._list, (self._key_getter(item), item)) 
            del self._list[i - 1]


    def __contains__(self, item):
        """
        Check if item is in collection.
        """
        return item in self._set


    def __len__(self):
        """
        Return length of collection.
        """
        return len(self._list)


    def __iter__(self):
        """
        Return iterator of sorted items.
        """
        return (item[1] for item in self._list)


    def __repr__(self):
        return 'Sorted(%s)' % list(self)
