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
from gaphas.decorators import nonrecursive, async, PRIORITY_HIGH_IDLE
from state import observed, reversible_method, reversible_pair
from gaphas.sorter import Sorter


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
    Container class for items.

    Attributes:
     - projector: canvas constraint projector between item and canvas
       coordinates
     - sorter: items sorter in order used to add items to canvas
    """

    def __init__(self):
        self._tree = tree.Tree()
        self._solver = solver.Solver()
        self._dirty_items = set()
        self._dirty_matrix_items = set()

        self._registered_views = set()

        self._sorter = Sorter(self._tree)

    sorter = property(lambda s: s._sorter)
    
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
        item._sort_key = self.sorter.get_key(item)

        for v in self._registered_views:
            v.update_matrix(item)

        self.request_update(item)
        self._update_views((item,))


    @observed
    def _remove(self, item):
        """
        Remove is done in a separate, @observed, method so the undo system
        can restore removed items in the right order.
        """
        item.canvas = None
        self._tree.remove(item)
        self.remove_connections_to_item(item)
        self._update_views((item,))
        self._dirty_items.discard(item)
        self._dirty_matrix_items.discard(item)

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
        for child in reversed(self.get_children(item)):
            self.remove(child)
        self._remove(item)

    reversible_pair(add, _remove,
                    bind1={'parent': lambda self, item: self.get_parent(item)})


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
            >>> c.get_all_items() # doctest: +ELLIPSIS
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
            >>> c.get_root_items() # doctest: +ELLIPSIS
            [<gaphas.item.Item ...>]
        """
        return self._tree.get_children(None)

    def reparent(self, item, parent):
        """
        Set new parent for an item.
        """
        self._tree.reparent(item, parent)


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
            >>> c.get_parent(ii) # doctest: +ELLIPSIS
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
            >>> list(c.get_ancestors(ii)) # doctest: +ELLIPSIS
            [<gaphas.item.Item ...>]
            >>> list(c.get_ancestors(iii)) # doctest: +ELLIPSIS
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
            >>> list(c.get_children(ii)) # doctest: +ELLIPSIS
            [<gaphas.item.Item ...>]
            >>> list(c.get_children(i)) # doctest: +ELLIPSIS
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
            >>> list(c.get_all_children(ii)) # doctest: +ELLIPSIS
            [<gaphas.item.Item ...>]
            >>> list(c.get_all_children(i)) # doctest: +ELLIPSIS
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
            >>> list(c.get_connected_items(ii)) # doctest: +ELLIPSIS
            [(<gaphas.item.Line ...>, <Handle object on (0, 0)>)]
            >>> list(c.get_connected_items(iii)) # doctest: +ELLIPSIS
            [(<gaphas.item.Line ...>, <Handle object on (0, 0)>)]
        """
        connected_items = set()
        for i in self.get_all_items():
            for h in i.handles():
                if h.connected_to is item:
                    connected_items.add((i, h))
        return connected_items

    def get_matrix_i2c(self, item, calculate=False):
        """
        Get the Item to World matrix for @item.

        item: The item who's item-to-world transformation matrix should be
              found
        calculate: True will allow this function to actually calculate it,
              in stead of raising an AttributeError when no matrix is present
              yet. Note that out-of-date matrices are not recalculated.
        """
        if item._matrix_i2c is None or calculate:
            self.update_matrix(item)
        return item._matrix_i2c


    def get_matrix_c2i(self, item, calculate=False):
        """
        Get the World to Item matrix for @item.
        See get_matrix_i2w().
        """
        if item._matrix_c2i is None or calculate:
            self.update_matrix(item)
        return item._matrix_c2i


    @observed
    def request_update(self, item, update=True, matrix=True):
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
        if update:
            self._dirty_items.add(item)
        if matrix:
            self._dirty_matrix_items.add(item)

        self.update()

    reversible_method(request_update, reverse=request_update)

#    @observed
    def request_matrix_update(self, item):
        """
        Schedule only the matrix to be updated.
        """
        self.request_update(item, update=False, matrix=True)

#    reversible_method(request_matrix_update, reverse=request_matrix_update)

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
        self.update_now()


    def _pre_update_items(self, items, context):
        context_map = dict()
        for item in items:
            c = Context(cairo=context)
            try:
                item.pre_update(c)
            except Exception, e:
                print 'Error while pre-updating item %s' % item
                import traceback
                traceback.print_exc()


    def _post_update_items(self, items, context):
        for item in items:
            c = Context(cairo=context)
            try:
                item.post_update(c)
            except Exception, e:
                print 'Error while updating item %s' % item
                import traceback
                traceback.print_exc()


    @nonrecursive
    def update_now(self):
        """
        Peform an update of the items that requested an update.
        """

        sort = self._sorter.sort

        # perform update requests for parents of dirty items
        dirty_items = self._dirty_items
        for item in set(dirty_items):
            dirty_items.update(self._tree.get_ancestors(item))

        # order the dirty items, so they are updated bottom to top
        dirty_items = sort(self._dirty_items, reverse=True)
        self._dirty_items.clear()

        try:
            context = self._obtain_cairo_context()

            # allow programmers to perform tricks and hacks before item
            # full update
            self._pre_update_items(dirty_items, context)

            # recalculate matrices
            dirty_matrix_items = self.update_matrices(self._dirty_matrix_items)
            self._dirty_matrix_items.clear()

            # request solving of external constraints associated with dirty
            # items
            request_resolve = self._solver.request_resolve
            for item in dirty_matrix_items:
                for h in item.handles():
                    request_resolve(h.x, projections_only=True)
                    request_resolve(h.y, projections_only=True)
            

            # solve all constraints
            self._solver.solve()

            # some item's can be marked dirty due to external constraints
            # solving;
            # NOTE: no matrix can change during constraint solving
            if self._dirty_items:
                dirty_items.extend(self._dirty_items)
                dirty_items = sort(dirty_items, reverse=True)
                self._dirty_items.clear()

            # normalize items, which changed after constraint solving;
            # store those items, which matrices changed
            c_dirty_matrix_items = self._normalize(dirty_items)

            # recalculate matrices of normalized items
            c_dirty_matrix_items = self.update_matrices(c_dirty_matrix_items)
            dirty_matrix_items.update(c_dirty_matrix_items)

            self._post_update_items(dirty_items, context)

        finally:
            assert len(self._dirty_items) == 0 and len(self._dirty_matrix_items) == 0, \
                'dirty: %s; matrix: %s' % (self._dirty_items, self._dirty_matrix_items)

            self._update_views(dirty_items, dirty_matrix_items)


    def update_matrices(self, items):
        """
        Recalculate matrices of the items. Items' children matrices are
        recalculated, too.

        Return items, which matrices were recalculated.
        """
        changed = set()
        for item in items:
            parent = self._tree.get_parent(item)
            if parent is not None and parent in items:
                # item's matrix will be updated thanks to parent's matrix
                # update
                continue

            self.update_matrix(item, parent)
            changed.add(item)

            for kid in self.get_all_children(item):
                self.update_matrix(kid, item)
                changed.add(kid)

        return changed


    def update_matrix(self, item, parent=None):
        """
        Update matrices of an item.
        """
        try:
            orig_matrix_i2c = Matrix(*item._matrix_i2c)
        except:
            orig_matrix_i2c = None

        item._matrix_i2c = Matrix(*item.matrix)

        if parent is not None:
            item._matrix_i2c *= self.get_matrix_i2c(parent)

        if orig_matrix_i2c is None or orig_matrix_i2c != item._matrix_i2c:
            # calculate c2i matrix and view matrices
            item._matrix_c2i = Matrix(*item._matrix_i2c)
            item._matrix_c2i.invert()
            for v in self._registered_views:
                v.update_matrix(item)


    def _normalize(self, items):
        """
        Update handle positions of items, so the first handle is always
        located at (0, 0).

        Return those items, which matrices changed due to first handle
        movement.

        For example having an item
        >>> from item import Element
        >>> c = Canvas()
        >>> e = Element()
        >>> c.add(e)
        >>> e.min_width = e.min_height = 0
        >>> c.update_now()
        >>> e.handles()
        [<Handle object on (0, 0)>, <Handle object on (10, 0)>, <Handle object on (10, 10)>, <Handle object on (0, 10)>]

        and moving its first handle a bit
        >>> e.handles()[0].x += 1
        >>> map(float, e.handles()[0].pos)
        [1.0, 0.0]

        After normalization
        >>> c._normalize([e])          # doctest: +ELLIPSIS
        set([<gaphas.item.Element object at ...>])
        >>> e.handles()
        [<Handle object on (0, 0)>, <Handle object on (9, 0)>, <Handle object on (9, 10)>, <Handle object on (-1, 10)>]
        """
        dirty_matrix_items = set()
        for item in items:
            handles = item.handles()
            if not handles:
                return dirty_matrix_items
            x, y = map(float, handles[0].pos)
            if x:
                item.matrix._matrix.translate(x, 0)
                dirty_matrix_items.add(item)
                for h in handles:
                    h.x._value -= x
            if y:
                item.matrix._matrix.translate(0, y)
                dirty_matrix_items.add(item)
                for h in handles:
                    h.y._value -= y

        return dirty_matrix_items


    def register_view(self, view):
        """
        Register a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.add(view)
        for item in self.get_all_items():
            view.update_matrix(item)


    def unregister_view(self, view):
        """
        Unregister a view on this canvas. This method is called when setting
        a canvas on a view and should not be called directly from user code.
        """
        self._registered_views.discard(view)

    def _update_views(self, dirty_items, dirty_matrix_items=()):
        """
        Send an update notification to all registered views.
        """
        for v in self._registered_views:
            v.request_update(dirty_items, dirty_matrix_items)

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


class VariableProjection(solver.Projection):
    """
    Project a single gaphas.solver.Variable to another space/coordinate system.

    The value has been set in the "other" coordinate system. A callback is
    executed when the value changes.
    
    It's a simple Variable-like class, following the Projection protocol:

    >>> def notify_me(val):
    ...     print 'new value', val
    >>> p = VariableProjection('var placeholder', 3.0, callback=notify_me)
    >>> p.value
    3.0
    >>> p.value = 6.5
    new value 6.5
    """

    def __init__(self, var, value, callback):
        self._var = var
        self._value = value
        self._callback = callback

    def _set_value(self, value):
        self._value = value
        self._callback(value)

    value = property(lambda s: s._value, _set_value)

    def variable(self):
        return self._var


class CanvasProjection(object):
    """
    Project a point as Canvas coordinates.
    Although this is a projection, it behaves like a tuple with two Variables
    (Projections).

    >>> canvas = Canvas()
    >>> from item import Element
    >>> a = Element()
    >>> canvas.add(a)
    >>> a.matrix.translate(30, 2)
    >>> canvas.request_matrix_update(a)
    >>> canvas.update_now()
    >>> canvas.get_matrix_i2c(a)
    cairo.Matrix(1, 0, 0, 1, 30, 2)
    >>> p = CanvasProjection(a.handles()[2].pos, a)
    >>> a.handles()[2].pos
    (Variable(10, 40), Variable(10, 40))
    >>> p[0].value
    40.0
    >>> p[1].value
    12.0
    >>> p[0].value = 63
    >>> p._point
    (Variable(33, 40), Variable(10, 40))

    TODO: How will this work on rotated variables?
    When the variables are retrieved, new values are calculated.
    """

    def __init__(self, point, item):
        self._point = point
        self._item = item

    def _on_change_x(self, value):
        item = self._item
        self._px = value
        self._point[0].value, self._point[1].value = item.canvas.get_matrix_c2i(item).transform_point(value, self._py)
        item.canvas.request_update(item, matrix=False)

    def _on_change_y(self, value):
        item = self._item
        self._py = value
        self._point[0].value, self._point[1].value = item.canvas.get_matrix_c2i(item).transform_point(self._px, value)
        item.canvas.request_update(item, matrix=False)

    def _get_value(self):
        """
        Return two delegating variables. Each variable should contain
        a value attribute with the real value.
        """
        x, y = self._point
        item = self._item
        self._px, self._py = item.canvas.get_matrix_i2c(item).transform_point(x, y)
        return self._px, self._py

    def __getitem__(self, key):
        return map(VariableProjection,
                   self._point, self._get_value(),
                   (self._on_change_x, self._on_change_y))[key]
        
    def __iter__(self):
        return iter(map(VariableProjection,
                        self._point, self._get_value(),
                        (self._on_change_x, self._on_change_y)))



# Additional tests in @observed methods
__test__ = {
    'Canvas.add': Canvas.add,
    'Canvas.remove': Canvas.remove,
    'Canvas.request_update': Canvas.request_update,
    }


if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)

# vim:sw=4:et
