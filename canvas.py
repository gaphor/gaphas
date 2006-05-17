"""
A Canvas owns a set of Items and acts as a container for both the items
and a constraint solver.
"""

__version__ = "$Revision$"
# $HeadURL$

import tree
import solver
from geometry import Matrix
from decorators import async, PRIORITY_HIGH_IDLE

class Context(object):
    """Context used for updating and drawing items in a drawing canvas.

        >>> c=Context(one=1,two='two')
        >>> c.one
        1
        >>> c.two
        'two'
        >>> try: c.one = 2
        ... except: 'got exc'
        'got exc'
    """
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def __setattr__(self, key, value):
        raise AttributeError, 'context is not writable'


class Canvas(object):
    """Container class for Items.
    """

    def __init__(self):
        self._tree = tree.Tree()
        self._solver = solver.Solver()
        self._dirty_items = set()
        self._dirty_matrix_items = set()
        self._in_update = False

        self._registered_views = set()

    solver = property(lambda s: s._solver)

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
        self.request_update(item)
        #self._dirty_items.add(item)
        #self._dirty_matrix_items.add(item)

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
        self._dirty_matrix_items.discard(item)
        

    def get_all_items(self):
        """Get a list of all items
        """
        return self._tree.nodes
    
    def get_root_items(self):
        """Return the root items of the canvas.
        """
        return self._tree.get_children(None)

    def get_parent(self, item):
        """See tree.Tree.get_parent()
        """
        return self._tree.get_parent(item)

    def get_ancestors(self, item):
        """See tree.Tree.get_ancestors()
        """
        return self._tree.get_ancestors(item)

    def get_children(self, item):
        """See tree.Tree.get_children()
        """
        return self._tree.get_children(item)

    def get_matrix_i2w(self, item):
        """Get the Item to World matrix for @item.
        """
        try:
            return item._canvas_matrix_i2w
        except AttributeError, e:
            self.request_matrix_update(item)
            raise e

    def get_matrix_w2i(self, item):
        """Get the World to Item matrix for @item.
        """
        try:
            return item._canvas_matrix_w2i
        except AttributeError, e:
            self.request_matrix_update(item)
            raise e

    def request_update(self, item):
        """Set an update request for the item. 

            >>> c = Canvas()
            >>> import item
            >>> i = item.Item()
            >>> ii = item.Item()
            >>> c.add(i)
            >>> c.add(ii, i)
            >>> len(c._dirty_items)
            2
            >>> c.update_now()
            >>> len(c._dirty_items)
            0
        """
        if True: #not self._in_update:
            self._dirty_items.add(item)
            self._dirty_matrix_items.add(item)

            # Also add update requests for parents of item
            parent = self._tree.get_parent(item)
            while parent:
                self._dirty_items.add(parent)
                parent = self._tree.get_parent(parent)

        # TODO: Schedule update, directly or through a view.
        self.update()

    def request_matrix_update(self, item):
        """Schedule only the matrix to be updated.
        """
        self._dirty_matrix_items.add(item)
        self.update()

    def require_update(self):
        """Returns True or False depending on if an update is needed.

            >>> c=Canvas()
            >>> c.require_update()
            False
            >>> import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> c.require_update()
            True
        """
        return bool(self._dirty_items)

    @async(single=True, priority=PRIORITY_HIGH_IDLE)
    def update(self):
        if not self._in_update:
            self.update_now()

    def update_now(self):
        """Peform an update of the items that requested an update.
        """
        self._in_update = True
        try:
            dirty_items = [ item for item in reversed(self._tree.nodes) \
                                 if item in self._dirty_items ]
            context_map = dict()
            for item in dirty_items:
                c = Context(parent=self._tree.get_parent(item),
                            children=self._tree.get_children(item))
                context_map[item] = c
                item.pre_update(c)

            self.update_matrices()

            self._solver.solve()

            dirty_items = [ item for item in reversed(self._tree.nodes) \
                                 if item in self._dirty_items ]

            self.update_matrices()

            #for item in dirty_items:
            #    item.update(context_map[item])
            for item in dirty_items:
                c = Context(parent=self._tree.get_parent(item),
                            children=self._tree.get_children(item))
                context_map[item] = c
                item.update(c)

        finally:
            self._update_views(dirty_items)
            self._dirty_items.clear()
            self._in_update = False

    def update_matrices(self):
        """Update the matrix of the items scheduled to be updated
        *and* their sub-items.

            >>> c = Canvas()
            >>> import item
            >>> i = item.Item()
            >>> ii = item.Item()
            >>> c.add(i)
            >>> i.matrix = (1.0, 0.0, 0.0, 1.0, 5.0, 0.0)
            >>> c.add(ii, i)
            >>> ii.matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 8.0)
            >>> c.update_matrices()
            >>> i._canvas_matrix_i2w
            cairo.Matrix(1, 0, 0, 1, 5, 0)
            >>> ii._canvas_matrix_i2w
            cairo.Matrix(1, 0, 0, 1, 5, 8)
            >>> len(c._dirty_items)
            2
        """
        dirty_items = self._dirty_matrix_items
        while dirty_items:
            item = dirty_items.pop()
            self.update_matrix(item)

    def update_matrix(self, item, recursive=True):
        """Update the World-to-Item (w2i) matrix for @item.
        This is stored as @item._canvas_matrix_i2w.
        @recursive == True will also update child objects.
        """
        parent = self._tree.get_parent(item)

        # First remove from the to-be-updated set.
        self._dirty_matrix_items.discard(item)

        if parent:
            if parent in self._dirty_matrix_items:
                self.update_matrix(parent)
            item._canvas_matrix_i2w = Matrix(*item.matrix)
            item._canvas_matrix_i2w *= parent._canvas_matrix_i2w
        else:
            item._canvas_matrix_i2w = Matrix(*item.matrix)

        # It's nice to have the W2I matrix present too:
        item._canvas_matrix_w2i = Matrix(*item._canvas_matrix_i2w)
        item._canvas_matrix_w2i.invert()

        if recursive:
            for child in self._tree.get_children(item):
                self.update_matrix(child, recursive)

    def register_view(self, view):
        """Register a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.add(view)

    def unregister_view(self, view):
        """Unregister a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.discard(view)

    def _update_views(self, items):
        """Send an update notification to all registered views.
        """
        for v in self._registered_views:
            v.request_update(items)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim:sw=4:et
