"""A Canvas owns a set of Items and acts as a container for both the items and
a constraint solver.

Connections
===========

Getting Connection Information
==============================
To get connected item to a handle::

    c = canvas.connections.get_connection(handle)
    if c is not None:
        print c.connected
        print c.port
        print c.constraint


To get all connected items (i.e. items on both sides of a line)::

    classes = (i.connected for i in canvas.get_connections(item=line))


To get connecting items (i.e. all lines connected to a class)::

    lines = (c.item for c in canvas.get_connections(connected=item))
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Optional

import cairo
from typing_extensions import Protocol

from gaphas import matrix, tree
from gaphas.connections import Connections
from gaphas.decorators import nonrecursive
from gaphas.state import observed, reversible_method, reversible_pair

if TYPE_CHECKING:
    from gaphas.item import Item
    from gaphas.view.model import View


class Context:
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
        raise AttributeError("context is not writable")


def instant_cairo_context():
    """A simple Cairo context, not attached to any window."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
    return cairo.Context(surface)


def default_update_context(item, cairo=instant_cairo_context()):
    return Context(cairo=cairo)


class Canvas:
    """Container class for items."""

    def __init__(self, create_update_context=default_update_context):
        self._create_update_context = create_update_context
        self._tree: tree.Tree[Item] = tree.Tree()
        self._connections = Connections()

        self._registered_views = set()

    solver = property(lambda s: s._connections.solver)

    connections = property(lambda s: s._connections)

    @observed
    def add(self, item, parent=None, index=None):
        """Add an item to the canvas.

        >>> c = Canvas()
        >>> from gaphas import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> len(c._tree.nodes)
        1
        >>> i._canvas is c
        True
        """
        assert item not in self._tree.nodes, f"Adding already added node {item}"

        self._tree.add(item, parent, index)
        self.request_update(item)

    @observed
    def _remove(self, item):
        """Remove is done in a separate, @observed, method so the undo system
        can restore removed items in the right order."""
        self._tree.remove(item)
        self._connections.disconnect_item(self)
        self._update_views(removed_items=(item,))

    def remove(self, item):
        """Remove item from the canvas.

        >>> c = Canvas()
        >>> from gaphas import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> c.remove(i)
        >>> c._tree.nodes
        []
        >>> i._canvas
        """
        for child in reversed(list(self.get_children(item))):
            self.remove(child)
        self._connections.remove_connections_to_item(item)
        self._remove(item)

    reversible_pair(
        add,
        _remove,
        bind1={
            "parent": lambda self, item: self.get_parent(item),
            "index": lambda self, item: self._tree.get_siblings(item).index(item),
        },
    )

    @observed
    def reparent(self, item, parent, index=None):
        """Set new parent for an item."""
        self._tree.move(item, parent, index)

    reversible_method(
        reparent,
        reverse=reparent,
        bind={
            "parent": lambda self, item: self.get_parent(item),
            "index": lambda self, item: self._tree.get_siblings(item).index(item),
        },
    )

    def get_all_items(self) -> Iterable[Item]:
        """Get a list of all items.

        >>> c = Canvas()
        >>> c.get_all_items()
        []
        >>> from gaphas import item
        >>> i = item.Item()
        >>> c.add(i)
        >>> c.get_all_items() # doctest: +ELLIPSIS
        [<gaphas.item.Item ...>]
        """
        return iter(self._tree.nodes)

    def get_root_items(self):
        """Return the root items of the canvas.

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

    def get_parent(self, item) -> Optional[Item]:
        """See `tree.Tree.get_parent()`.

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

    def get_children(self, item) -> Iterable[Item]:
        """See `tree.Tree.get_children()`.

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

    def sort(self, items) -> Iterable[Item]:
        """Sort a list of items in the order in which they are traversed in the
        canvas (Depth first).

        >>> c = Canvas()
        >>> from gaphas import item
        >>> i1 = item.Line()
        >>> c.add(i1)
        >>> i2 = item.Line()
        >>> c.add(i2)
        >>> i3 = item.Line()
        >>> c.add (i3)
        >>> c.update_now((i1, i2, i3)) # ensure items are indexed
        >>> s = c.sort([i2, i3, i1])
        >>> s[0] is i1 and s[1] is i2 and s[2] is i3
        True
        """
        return self._tree.order(items)

    def get_matrix_i2c(self, item: Item) -> matrix.Matrix:
        """Get the Item to Canvas matrix for ``item``.

        item:
            The item who's item-to-canvas transformation matrix should
            be found
        calculate:
            True will allow this function to actually calculate it,
            instead of raising an `AttributeError` when no matrix is
            present yet. Note that out-of-date matrices are not
            recalculated.
        """
        m = item.matrix

        parent = self._tree.get_parent(item)
        if parent is not None:
            m = m.multiply(self.get_matrix_i2c(parent))
        return m

    @observed
    def request_update(self, item, update=True, matrix=True):
        """Set an update request for the item.

        >>> c = Canvas()
        >>> from gaphas import item
        >>> i = item.Item()
        >>> ii = item.Item()
        >>> c.add(i)
        >>> c.add(ii, i)
        >>> len(c._dirty_items)
        0
        >>> c.update_now((i, ii))
        >>> len(c._dirty_items)
        0
        """
        if update and matrix:
            self._update_views(dirty_items=(item,), dirty_matrix_items=(item,))
        elif update:
            self._update_views(dirty_items=(item,))
        elif matrix:
            self._update_views(dirty_matrix_items=(item,))

    reversible_method(request_update, reverse=request_update)

    def request_matrix_update(self, item):
        """Schedule only the matrix to be updated."""
        self.request_update(item, update=False, matrix=True)

    def _pre_update_items(self, items):
        create_update_context = self._create_update_context
        contexts = {}
        for item in items:
            context = create_update_context(item)
            item.pre_update(context)
            contexts[item] = context
        return contexts

    def _post_update_items(self, items, contexts):
        create_update_context = self._create_update_context
        for item in items:
            context = contexts.get(item)
            if not context:
                context = create_update_context(item)
            item.post_update(context)

    @nonrecursive
    def update_now(self, dirty_items, dirty_matrix_items=()):
        """Perform an update of the items that requested an update."""
        sort = self.sort

        def dirty_items_with_ancestors():
            for item in set(dirty_items):
                yield item
                yield from self._tree.get_ancestors(item)

        all_dirty_items = list(reversed(list(sort(dirty_items_with_ancestors()))))

        try:
            # allow programmers to perform tricks and hacks before item
            # full update (only called for items that requested a full update)
            contexts = self._pre_update_items(all_dirty_items)

            # keep it here, since we need up to date matrices for the solver
            for d in dirty_items:
                d.matrix_i2c.set(*self.get_matrix_i2c(d))
            for d in dirty_matrix_items:
                d.matrix_i2c.set(*self.get_matrix_i2c(d))

            # solve all constraints
            self.solver.solve()

            self._post_update_items(all_dirty_items, contexts)

        except Exception as e:
            logging.error("Error while updating canvas", exc_info=e)

    def register_view(self, view: View):
        """Register a view on this canvas.

        This method is called when setting a canvas on a view and should
        not be called directly from user code.
        """
        self._registered_views.add(view)

    def unregister_view(self, view: View):
        """Unregister a view on this canvas.

        This method is called when setting a canvas on a view and should
        not be called directly from user code.
        """
        self._registered_views.discard(view)

    def _update_views(self, dirty_items=(), dirty_matrix_items=(), removed_items=()):
        """Send an update notification to all registered views."""
        for v in self._registered_views:
            v.request_update(dirty_items, dirty_matrix_items, removed_items)


class Traversable(Protocol):
    def get_parent(self, item: Item) -> Optional[Item]:
        ...

    def get_children(self, item: Optional[Item]) -> Iterable[Item]:
        ...


def ancestors(canvas: Traversable, item: Item) -> Iterable[Optional[Item]]:
    parent = canvas.get_parent(item)
    while parent:
        yield parent
        parent = canvas.get_parent(parent)


def all_children(canvas: Traversable, item: Optional[Item]) -> Iterable[Item]:
    children = canvas.get_children(item)
    for child in children:
        yield child
        yield from all_children(canvas, child)


# Additional tests in @observed methods
__test__ = {
    "Canvas.add": Canvas.add,
    "Canvas.remove": Canvas.remove,
    "Canvas.request_update": Canvas.request_update,
}
