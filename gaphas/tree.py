"""Simple class containing the tree structure for the canvas items."""

from __future__ import annotations

from contextlib import suppress
from typing import Generic, Iterable, Sequence, TypeVar

T = TypeVar("T")


class Tree(Generic[T]):
    """A Tree structure. Nodes are stores in a depth-first order.

    ``None`` is the root node.

    @invariant: len(self._children) == len(self._nodes) + 1
    """

    def __init__(self) -> None:
        # List of nodes in the tree, sorted in the order they ought to be
        # rendered
        self._nodes: list[T] = []

        # Per entry a list of children is maintained.
        self._children: dict[T | None, list[T]] = {None: []}

        # For easy and fast lookups, also maintain a child -> parent mapping
        self._parents: dict[T, T] = {}

    @property
    def nodes(self) -> Sequence[T]:
        return list(self._nodes)

    def get_parent(self, node: T) -> T | None:
        """Return the parent item of ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.get_parent('n2')
        'n1'
        """
        return self._parents.get(node)

    def get_children(self, node: T | None) -> Iterable[T]:
        """Return all child objects of ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.get_children('n1')
        ['n2', 'n3']
        >>> tree.get_children('n2')
        []
        """
        return self._children[node]

    def get_siblings(self, node: T) -> list[T]:
        """Get all siblings of ``node``, including ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.get_siblings('n2')
        ['n2', 'n3']
        """
        parent = self.get_parent(node)
        return self._children[parent]

    def get_next_sibling(self, node: T) -> T:
        """Return the node on the same level after ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.get_next_sibling('n2')
        'n3'
        >>> tree.get_next_sibling('n3') # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        IndexError: list index out of range
        """
        parent = self.get_parent(node)
        siblings = self._children[parent]
        return siblings[siblings.index(node) + 1]

    def get_previous_sibling(self, node: T) -> T:
        """Return the node on the same level before ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.get_previous_sibling('n3')
        'n2'
        >>> tree.get_previous_sibling('n2') # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        IndexError: list index out of range
        """
        parent = self.get_parent(node)
        siblings = self._children[parent]
        index = siblings.index(node) - 1
        if index < 0:
            raise IndexError("list index out of range")
        return siblings[index]

    def get_all_children(self, node: T) -> Iterable[T]:
        """Iterate all children (and children of children and so forth)

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n2')
        >>> tree.get_children('n1')
        ['n2']
        >>> tree.get_all_children('n1') # doctest: +ELLIPSIS
        <generator object Tree.get_all_children at 0x...>
        >>> list(tree.get_all_children('n1'))
        ['n2', 'n3']
        """
        children = self.get_children(node)
        for c in children:
            yield c
            yield from self.get_all_children(c)

    def get_ancestors(self, node: T) -> Iterable[T]:
        """Iterate all parents and parents of parents, etc.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n2')
        >>> tree.get_parent('n3')
        'n2'
        >>> tree.get_ancestors('n3') # doctest: +ELLIPSIS
        <generator object Tree.get_ancestors at 0x...>
        >>> list(tree.get_ancestors('n3'))
        ['n2', 'n1']
        >>> list(tree.get_ancestors('n1'))
        []
        """
        parent = self.get_parent(node)
        while parent:
            yield parent
            parent = self.get_parent(parent)

    def order(self, items: Iterable[T]) -> Iterable[T]:
        items_set = set(items)
        return (n for n in self._nodes if n in items_set)

    def _add_to_nodes(
        self, node: T, parent: T | None, index: int | None = None
    ) -> None:
        """Helper method to place nodes on the right location in the nodes list
        Called only from add() and move()"""
        nodes = self._nodes
        siblings = self._children[parent]
        try:
            atnode = siblings[index]  # type: ignore[index]
        except (TypeError, IndexError):
            index = len(siblings)
            if parent:
                try:
                    next_uncle = self.get_next_sibling(parent)
                except IndexError:
                    # parent has no younger brothers..
                    # place it before the next uncle of grant_parent:
                    return self._add_to_nodes(node, self.get_parent(parent))
                else:
                    nodes.insert(nodes.index(next_uncle), node)
            else:
                # append to root node:
                nodes.append(node)
        else:
            nodes.insert(nodes.index(atnode), node)

    def _add(self, node: T, parent: T | None = None, index: int | None = None) -> None:
        """Helper method for both add() and move()."""
        assert node not in self._nodes

        siblings = self._children[parent]

        self._add_to_nodes(node, parent, index)

        # Fix parent-child and child-parent relationship
        try:
            siblings.insert(index, node)  # type: ignore[arg-type]
        except TypeError:
            siblings.append(node)

        # Create new entry for it's own children:
        if parent:
            self._parents[node] = parent

    def add(self, node: T, parent: T | None = None, index: int | None = None) -> None:
        """Add node to the tree. parent is the parent node, which may be None
        if the item should be added to the root item.

        For usage, see the unit tests.
        """
        self._add(node, parent, index)
        self._children[node] = []

    def _remove(self, node: T) -> None:
        # Remove from parent item
        self.get_siblings(node).remove(node)
        # Remove data entries:
        del self._children[node]
        self._nodes.remove(node)
        with suppress(KeyError):
            del self._parents[node]

    def remove(self, node: T) -> None:
        """Remove ``node`` from the tree.

        For usage, see the unit tests.
        """
        # First remove children:
        for c in reversed(list(self._children[node])):
            self.remove(c)
        self._remove(node)

    def _reparent_nodes(self, node: T, parent: T | None) -> None:
        """Helper for move().

        The _children and _parent trees can be left intact as far as
        children of the reparented node are concerned. Only the position
        in the _nodes list changes.
        """
        self._nodes.remove(node)
        self._add_to_nodes(node, parent)
        for c in self._children[node]:
            self._reparent_nodes(c, node)

    def move(self, node: T, parent: T | None, index: int | None = None) -> None:
        """Set new parent for a ``node``. ``Parent`` can be ``None``,
        indicating it's added to the top.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.nodes
        ['n1', 'n2', 'n3']
        >>> tree.move('n2', 'n3')
        >>> tree.get_parent('n2')
        'n3'
        >>> tree.get_children('n3')
        ['n2']
        >>> tree.nodes
        ['n1', 'n3', 'n2']

        If a node contains children, those are also moved:

        >>> tree.add('n4')
        >>> tree.nodes
        ['n1', 'n3', 'n2', 'n4']
        >>> tree.move('n1', 'n4')
        >>> tree.get_parent('n1')
        'n4'
        >>> list(tree.get_all_children('n4'))
        ['n1', 'n3', 'n2']
        >>> tree.nodes
        ['n4', 'n1', 'n3', 'n2']
        """
        if parent is self.get_parent(node):
            return

        # Remove all node references:
        old_parent = self.get_parent(node)
        self._children[old_parent].remove(node)
        self._nodes.remove(node)
        if old_parent:
            del self._parents[node]

        self._add(node, parent, index)

        # reorganize children in nodes list
        for c in self._children[node]:
            self._reparent_nodes(c, node)
