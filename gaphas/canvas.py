"""
A Canvas owns a set of Items and acts as a container for both the items
and a constraint solver.
"""

__version__ = "$Revision$"
# $HeadURL$


import cairo
from cairo import Matrix
from gaphas import tree
from gaphas import solver
from gaphas.decorators import async, PRIORITY_HIGH_IDLE
from state import observed, reversible_method, reversible_pair


class Context(object):
    """
    Context used for updating and drawing items in a drawing canvas.

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
    """
    Container class for Items.
    """

    def __init__(self):
        self._tree = tree.Tree()
        self._solver = solver.Solver()
        self._dirty_items = set()
        self._dirty_matrix_items = set()
        self._in_update = False

        self._registered_views = set()

    solver = property(lambda s: s._solver)

    @observed
    def add(self, item, parent=None):
        """
        Add an item to the canvas

            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> len(c._tree.nodes)
            1
            >>> i._canvas is c
            True
        """
        assert item not in self._tree.nodes, 'Adding already added node %s' % item
        item.canvas = self
        self._tree.add(item, parent)
        self.request_update(item)

    @observed
    def remove(self, item):
        """
        Remove item from the canvas

            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> c.remove(i)
            >>> c._tree.nodes
            []
            >>> i._canvas
        """
        self._tree.remove(item)
        item.canvas = None
        self.remove_connections_to_item(item)
        self._update_views((item,))
        self._dirty_items.discard(item)
        self._dirty_matrix_items.discard(item)

    reversible_pair(add, remove,
                    bind1={'parent': lambda self, node: self.get_parent(node) })

    def remove_connections_to_item(self, item):
        """
        Remove all connections (handles connected to and constraints)
        for a specific item.
        This is some brute force cleanup (e.g. if constraints are referenced
        by items, those references are not cleaned up).

        This method implies the constraint used to keep the handle in place
        is connected to Handle.connect_constraint.
        """
        for i, h in self.get_connected_items(item):
            #self._solver.remove_constraint(h.connect_constraint)
            h.disconnect()
            # Never mind..
            h.connected_to = None
            h.disconnect = lambda: 0

    def get_all_items(self):
        """
        Get a list of all items
            >>> c = Canvas()
            >>> c.get_all_items()
            []
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> c.get_all_items()
            [<gaphas.item.Item ...>]

        """
        return self._tree.nodes
    
    def get_root_items(self):
        """
        Return the root items of the canvas.

            >>> c = Canvas()
            >>> c.get_all_items()
            []
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> ii = item.Item()
            >>> c.add(ii, i)
            >>> c.get_root_items()
            [<gaphas.item.Item ...>]
        """
        return self._tree.get_children(None)

    def get_parent(self, item):
        """
        See tree.Tree.get_parent()
            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> ii = item.Item()
            >>> c.add(ii, i)
            >>> c.get_parent(i)
            >>> c.get_parent(ii)
            <gaphas.item.Item ...>
        """
        return self._tree.get_parent(item)

    def get_ancestors(self, item):
        """
        See tree.Tree.get_ancestors()
            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> ii = item.Item()
            >>> c.add(ii, i)
            >>> iii = item.Item()
            >>> c.add(iii, ii)
            >>> list(c.get_ancestors(i))
            []
            >>> list(c.get_ancestors(ii))
            [<gaphas.item.Item ...>]
            >>> list(c.get_ancestors(iii))
            [<gaphas.item.Item ...>, <gaphas.item.Item ...>]
        """
        return self._tree.get_ancestors(item)

    def get_children(self, item):
        """
        See tree.Tree.get_children()
            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> ii = item.Item()
            >>> c.add(ii, i)
            >>> iii = item.Item()
            >>> c.add(iii, ii)
            >>> list(c.get_children(iii))
            []
            >>> list(c.get_children(ii))
            [<gaphas.item.Item ...>]
            >>> list(c.get_children(i))
            [<gaphas.item.Item ...>]
        """
        return self._tree.get_children(item)

    def get_all_children(self, item):
        """
        See tree.Tree.get_all_children()
            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> ii = item.Item()
            >>> c.add(ii, i)
            >>> iii = item.Item()
            >>> c.add(iii, ii)
            >>> list(c.get_all_children(iii))
            []
            >>> list(c.get_all_children(ii))
            [<gaphas.item.Item ...>]
            >>> list(c.get_all_children(i))
            [<gaphas.item.Item ...>, <gaphas.item.Item ...>]
        """
        return self._tree.get_all_children(item)

    def get_connected_items(self, item):
        """
        Return a set of items that are connected to @item.
        The list contains tuples (item, handle). As a result an item may be
        in the list more than once (depending on the number of handles that
        are connected). If @item is connected to itself it will also appear
        in the list.

            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Line()
            >>> c.add(i)
            >>> ii = item.Line()
            >>> c.add(ii)
            >>> iii = item.Line()
            >>> c.add (iii)
            >>> i.handles()[0].connected_to = ii
            >>> list(c.get_connected_items(i))
            []
            >>> ii.handles()[0].connected_to = iii
            >>> list(c.get_connected_items(ii))
            [(<gaphas.item.Line ...>, <Handle object on (0, 0)>)]
            >>> list(c.get_connected_items(iii))
            [(<gaphas.item.Line ...>, <Handle object on (0, 0)>)]
        """
        connected_items = set()
        for i in self.get_all_items():
            for h in i.handles():
                if h.connected_to is item:
                    connected_items.add((i, h))
        return connected_items

    def get_matrix_i2w(self, item, calculate=False):
        """
        Get the Item to World matrix for @item.

        item: The item who's item-to-world transformation matrix should be
              found
        calculate: True will allow this function to actually calculate it,
              in stead of raising an AttributeError when no matrix is present
              yet. Note that out-of-date matrices are not recalculated.
        """
        try:
            return item._canvas_matrix_i2w
        except AttributeError, e:
            if calculate:
                self.update_matrix(item, recursive=False)
                return item._canvas_matrix_i2w
            else:
                self.request_matrix_update(item)
                raise e

    def get_matrix_w2i(self, item, calculate=False):
        """
        Get the World to Item matrix for @item.
        See get_matrix_i2w().
        """
        try:
            return item._canvas_matrix_w2i
        except AttributeError, e:
            if calculate:
                self.update_matrix(item, recursive=False)
                return item._canvas_matrix_w2i
            else:
                self.request_matrix_update(item)
                raise e

    @observed
    def request_update(self, item):
        """
        Set an update request for the item. 

            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> ii = item.Item()
            >>> c.add(i)
            >>> c.add(ii, i)
            >>> len(c._dirty_items)
            0
            >>> c.update_now()
            >>> len(c._dirty_items)
            0
        """
        if True:
            self._dirty_items.add(item)
            self._dirty_matrix_items.add(item)

            # Also add update requests for parents of item
            parent = self._tree.get_parent(item)
            while parent:
                self._dirty_items.add(parent)
                parent = self._tree.get_parent(parent)
        self.update()

    reversible_method(request_update, reverse=request_update)

    def request_matrix_update(self, item):
        """
        Schedule only the matrix to be updated.
        """
        self._dirty_matrix_items.add(item)
        self.update()

    def require_update(self):
        """
        Returns True or False depending on if an update is needed.

            >>> c=Canvas()
            >>> c.require_update()
            False
            >>> from gaphas import item
            >>> i = item.Item()
            >>> c.add(i)
            >>> c.require_update()
            False

        Since we're not in a GTK+ mainloop, the update is not scheduled
        asynchronous. Therefor require_update() returns False.
        """
        return bool(self._dirty_items)

    @async(single=True, priority=PRIORITY_HIGH_IDLE)
    def update(self):
        """
        Update the canvas, if called from within a gtk-mainloop, the
        update job is scheduled as idle job.
        """
        if not self._in_update:
            self.update_now()

    def update_now(self):
        """
        Peform an update of the items that requested an update.
        """
        self._in_update = True
        dirty_items = []
        try:
            cairo_context = self._obtain_cairo_context()

            dirty_items = [ item for item in reversed(self._tree.nodes) \
                                 if item in self._dirty_items ]
            context_map = dict()
            for item in dirty_items:
                c = Context(parent=self._tree.get_parent(item),
                            children=self._tree.get_children(item),
                            cairo=cairo_context)
                context_map[item] = c
                try:
                    item.pre_update(c)
                except Exception, e:
                    print 'Error while updating item %s' % item
                    import traceback
                    traceback.print_exc()

            self.update_matrices()

            self._solver.solve()

            dirty_items = [ item for item in reversed(self._tree.nodes) \
                                 if item in self._dirty_items ]

            self.update_matrices()

            for item in dirty_items:
                c = Context(parent=self._tree.get_parent(item),
                            children=self._tree.get_children(item),
                            cairo=cairo_context)
                context_map[item] = c
                try:
                    item.update(c)
                except Exception, e:
                    print 'Error while updating item %s' % item
                    import traceback
                    traceback.print_exc()

        finally:
            self._update_views(dirty_items)
            self._dirty_items.clear()
            self._in_update = False

    def update_matrices(self):
        """
        Update the matrix of the items scheduled to be updated
        *and* their sub-items.

            >>> c = Canvas()
            >>> from gaphas import item
            >>> i = item.Item()
            >>> ii = item.Item()
            >>> i.matrix = (1.0, 0.0, 0.0, 1.0, 5.0, 0.0)
            >>> c.add(i)
            >>> ii.matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 8.0)
            >>> c.add(ii, i)
            >>> c.update_matrices()
            >>> i._canvas_matrix_i2w
            cairo.Matrix(1, 0, 0, 1, 5, 0)
            >>> ii._canvas_matrix_i2w
            cairo.Matrix(1, 0, 0, 1, 5, 8)
            >>> len(c._dirty_items)
            0
        """
        dirty_items = self._dirty_matrix_items
        while dirty_items:
            item = dirty_items.pop()
            self.update_matrix(item)

    def update_matrix(self, item, recursive=True):
        """
        Update the World-to-Item (w2i) matrix for @item.
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
        """
        Register a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.add(view)

    def unregister_view(self, view):
        """
        Unregister a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.discard(view)

    def _update_views(self, items):
        """
        Send an update notification to all registered views.
        """
        for v in self._registered_views:
            v.request_update(items)

    def _obtain_cairo_context(self):
        """
        Try to obtain a Cairo context.

        This is a not-so-clean way to solve issues like calculating the
        bounding box for a piece of text (for that you'll need a CairoContext).
        The Cairo context is created by a View registered as view on this
        canvas. By lack of registered views, a PNG image surface is created
        that is used to create a context.

            >>> c = Canvas()
            >>> c.update_now()
        """
        for view in self._registered_views:
            try:
                return view.window.cairo_create()
            except AttributeError:
                pass
        else:
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
            return cairo.Context(surface)


if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)

# vim:sw=4:et
