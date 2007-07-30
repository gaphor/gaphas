"""
Simple class containing the tree structure for the canvas items.

"""

__version__ = "$Revision$"
# $HeadURL$

import operator
from state import observed, reversible_method, \
        reversible_pair, disable_dispatching


class Tree(object):
    """
    A Tree structure.
    None is the root node.

    @invariant: len(self._children) == len(self._nodes) + 1
    """

    def __init__(self):
        # List of nodes in the tree, sorted in the order they ought to be
        # rendered
        self._nodes = []

        # Per entry a list of children is maintained.
        self._children = { None: [] }

        # For easy and fast lookups, also maintain a child -> parent mapping
        self._parents = { }

    nodes = property(lambda s: list(s._nodes))

    def get_parent(self, node):
        """
        Return the parent item of ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.get_parent('n2')
        'n1'
        """
        return self._parents.get(node)

    def get_children(self, node):
        """
        Return all child objects of ``node``.

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

    def get_siblings(self, node):
        """
        Get all siblings of ``node``, including ``node``.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.get_siblings('n2')
        ['n2', 'n3']
        """
        parent = self.get_parent(node)
        return self._children[parent]

    def get_next_sibling(self, node):
        """
        Return the node on the same level after ``node``.

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

    def get_previous_sibling(self, node):
        """
        Return the node on the same level before ``node``.

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
            raise IndexError('list index out of range')
        return siblings[index]

    def get_all_children(self, node):
        """
        Iterate all children (and children of children and so forth)

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n2')
        >>> tree.get_children('n1')
        ['n2']
        >>> tree.get_all_children('n1') # doctest: +ELLIPSIS
        <generator object at 0x...>
        >>> list(tree.get_all_children('n1'))
        ['n2', 'n3']
        """
        children = self.get_children(node)
        for c in children:
            yield c
            for cc in self.get_all_children(c):
                yield cc

    def get_ancestors(self, node):
        """
        Iterate all parents and parents of parents, etc.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n2')
        >>> tree.get_parent('n3')
        'n2'
        >>> tree.get_ancestors('n3') # doctest: +ELLIPSIS
        <generator object at 0x...>
        >>> list(tree.get_ancestors('n3'))
        ['n2', 'n1']
        >>> list(tree.get_ancestors('n1'))
        []
        """
        parent = self.get_parent(node)
        while parent:
            yield parent
            parent = self.get_parent(parent)

    def _add_to_nodes(self, node, parent):
        """
        Called only from add()
        """
        nodes = self._nodes
        if parent:
            try:
                next_uncle = self.get_next_sibling(parent)
            except IndexError:
                # parent has no younger brothers..
                # place it before the next uncle of grant_parent:
                self._add_to_nodes(node, self.get_parent(parent))
            else:
                nodes.insert(nodes.index(next_uncle), node)
        else:
            # append to root node:
            nodes.append(node)

    @observed
    def add(self, node, parent=None):
        """
        Add node to the tree. parent is the parent node, which may
        be None if the item should be added to the root item.

        For usage, see the unit tests.
        """
        assert not self._children.get(node)
        siblings = self._children[parent]
        self._add_to_nodes(node, parent)
        siblings.append(node)
        # Create new entry for it's own children:
        self._children[node] = []
        if parent:
            self._parents[node] = parent

    @observed
    def _remove(self, node):
        # Remove from parent item
        self.get_siblings(node).remove(node)
        # Remove data entries:
        del self._children[node]
        self._nodes.remove(node)
        try:
            del self._parents[node]
        except KeyError:
            pass

    def remove(self, node):
        """
        Remove ``node`` from the tree.

        For usage, see the unit tests.
        """
        # First remove children:
        for c in reversed(list(self._children[node])):
            self.remove(c)
        self._remove(node)

    def _reparent_nodes(self, node, parent):
        """
        Helper for reparent().
        The _children and _parent trees can be left intact as far as children
        of the reparented node are concerned. Only the position in the
        _nodes list changes.
        """
        self._nodes.remove(node)
        self._add_to_nodes(node, parent)
        for c in self._children[node]:
            self._reparent_nodes(c, node)
        
    @observed
    def reparent(self, node, parent):
        """
        Set new parent for a ``node``. ``Parent`` can be ``None``, indicating
        it's added to the top.

        >>> tree = Tree()
        >>> tree.add('n1')
        >>> tree.add('n2', parent='n1')
        >>> tree.add('n3', parent='n1')
        >>> tree.nodes
        ['n1', 'n2', 'n3']
        >>> tree.reparent('n2', 'n3')
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
        >>> tree.reparent('n1', 'n4')
        >>> tree.get_parent('n1')
        'n4'
        >>> list(tree.get_all_children('n4'))
        ['n1', 'n3', 'n2']
        >>> tree.nodes
        ['n4', 'n1', 'n3', 'n2']
        """
        # Add to new parent's children:
        self.get_siblings(node).remove(node)
        self._children[parent].append(node)
        self._parents[node] = parent
        
        # reorganize nodes
        self._reparent_nodes(node, parent)


    reversible_pair(add, _remove,
            bind1={'parent': lambda self, node: self.get_parent(node) })

    reversible_method(reparent, reverse=reparent,
            bind={'parent': lambda self, node: self.get_parent(node) })

    # Disable add/remove by default, since they are handled by canvas.Canvas
    disable_dispatching(add)
    disable_dispatching(_remove)


__test__ = {
    'Tree.add': Tree.add,
    'Tree.remove': Tree.remove,
    'Tree.reparent': Tree.reparent,
    }


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vi:sw=4:et
