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
from typing import Iterable, Protocol

import cairo

from gaphas import matrix, tree
from gaphas.connections import Connection, Connections
from gaphas.item import Item
from gaphas.model import View


def instant_cairo_context():
    """A simple Cairo context, not attached to any window."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
    return cairo.Context(surface)


class Canvas:
    """Container class for items."""

    def __init__(self):
        self._tree: tree.Tree[Item] = tree.Tree()
        self._connections = Connections()

        self._registered_views = set()
        self._connections.add_handler(self._on_constraint_solved)

    @property
    def solver(self):
        return self._connections.solver

    @property
    def connections(self) -> Connections:
        return self._connections

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

    def _remove(self, item):
        """Remove is done in a separate, @observed, method so the undo system
        can restore removed items in the right order."""
        self._tree.remove(item)
        self._connections.disconnect_item(item)
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

    def reparent(self, item, parent, index=None):
        """Set new parent for an item."""
        self._tree.move(item, parent, index)

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

    def get_parent(self, item: Item) -> Item | None:
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

    def get_children(self, item: Item | None) -> Iterable[Item]:
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

    def sort(self, items: Iterable[Item]) -> Iterable[Item]:
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

    def request_update(self, item: Item) -> None:
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
        self._update_views(dirty_items=(item,))

    def request_matrix_update(self, item):
        """Schedule only the matrix to be updated."""
        self.request_update(item)

    def update_now(self, dirty_items):
        """Perform an update of the items that requested an update."""
        try:
            # keep it here, since we need up to date matrices for the solver
            for d in dirty_items:
                d.matrix_i2c.set(*self.get_matrix_i2c(d))

            # solve all constraints
            self._connections.solve()

        except Exception as e:
            logging.error("Error while updating canvas", exc_info=e)

    def register_view(self, view: View) -> None:
        """Register a view on this canvas.

        This method is called when setting a canvas on a view and should
        not be called directly from user code.
        """
        self._registered_views.add(view)

    def unregister_view(self, view: View) -> None:
        """Unregister a view on this canvas.

        This method is called when setting a canvas on a view and should
        not be called directly from user code.
        """
        self._registered_views.discard(view)

    def _on_constraint_solved(self, cinfo: Connection) -> None:
        dirty_items = set()
        known_items = set(self._tree.nodes)
        item = cinfo.item
        if item and item in known_items:
            dirty_items.add(item)
        connected = cinfo.connected
        if connected and connected in known_items:
            dirty_items.add(connected)
        if dirty_items:
            self._update_views(dirty_items)

    def _update_views(self, dirty_items=(), removed_items=()):
        """Send an update notification to all registered views."""
        for v in self._registered_views:
            v.request_update(dirty_items, removed_items)


class Traversable(Protocol):
    def get_parent(self, item: Item) -> Item | None: ...

    def get_children(self, item: Item | None) -> Iterable[Item]: ...


def ancestors(canvas: Traversable, item: Item) -> Iterable[Item | None]:
    parent = canvas.get_parent(item)
    while parent:
        yield parent
        parent = canvas.get_parent(parent)


def all_children(canvas: Traversable, item: Item | None) -> Iterable[Item]:
    children = canvas.get_children(item)
    for child in children:
        yield child
        yield from all_children(canvas, child)
