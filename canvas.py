"""
A Canvas owns a set of Items and acts as a container for both the items
and a constraint solver.
"""

import tree
import solver

class Canvas(object):
    """Container class for Items.
    """

    def __init__(self):
        self._tree = tree.Tree()
        self._solver = solver.Solver()
        self._dirty_items = set()
        self._in_update = False

    def add(self, item, parent=None):
        """Add an item to the canvas
        >>> c = Canvas()
        >>> import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> len(c._tree.nodes)
        1
        >>> i._canvas is c
        True
        """
        item.canvas = self
        self._tree.add(item, parent)
        self._dirty_items.add(item)

    def remove(self, item):
        """Remove item from the canvas
        >>> c = Canvas()
        >>> import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> c.remove(i)
        >>> c._tree.nodes
        []
        >>> i._canvas
        """
        self._tree.remove(item)
        item.canvas = None
        self._dirty_items.discard(item)
        

    def request_update(self, item):
        """Set an update request for the item. 
        """
        if not self._in_update:
            self._dirty_items.add(item)

            # Also add update requests for parents of item
            parent = self._tree.get_parent(item)
            while parent:
                self._dirty_items.add(parent)
                parent = self._tree.get_parent(parent)

        # TODO: Schedule update, directly or through a view.

    def update_needed(self):
        """Returns True or False depending on if an update is needed.
        >>> c=Canvas()
        >>> c.update_needed()
        False
        >>> import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> c.update_needed()
        True
        """
        return len(self._dirty_items) > 0

    def update_now(self):
        """Peform an update of the items that requested an update.
        """
        self._in_update = True
        try:
            dirty_items = [ item for item in reversed(self._tree.nodes) \
                                 if item in self._dirty_items ]
            for item in dirty_items:
                # TODO: calculate context.matrix_i2w
                item.pre_update(context)

            self._solver.solve()

            for item in dirty_items:
                item.update(context)
        finally:
            self._dirty_items.clear()
            self._in_update = False

    def get_matrix_i2w(self, item):
	matrix = item.matrix
	
if __name__ == '__main__':
    import doctest
    doctest.testmod()
