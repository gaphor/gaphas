"""
Simple class containing the tree structure for the canvas items.

"""

__version__ = "$Revision$"
# $HeadURL$

from state import observed, reversible_pair, disable_dispatching


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

    nodes = property(lambda s: list(s._nodes))

    def get_parent(self, node):
        """
        Return the parent item of @node.
        """
        for item, children in self._children.items():
            if node in children:
                return item

    def get_children(self, node):
        """
        Return all child objects of @node.
        """
        return self._children[node]

    def get_siblings(self, node):
        """
        Get all siblings of @node, including @node.
        """
        parent = self.get_parent(node)
        return self._children[parent]

    def get_next_sibling(self, node):
        """
        Return the node on the same level after @node.
        """
        parent = self.get_parent(node)
        siblings = self._children[parent]
        return siblings[siblings.index(node) + 1]

    def get_previous_sibling(self, node):
        """
        Return the node on the same level before @node.
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
        """
        children = self.get_children(node)
        for c in children:
            yield c
            for cc in self.get_all_children(c):
                yield cc

    def get_ancestors(self, node):
        """
        Iterate all parents and parents of parents, etc.
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
        Add @node to the tree. @parent is the parent node, which may
        be None if the item should be added to the root item.
        """
        assert not self._children.get(node)
        siblings = self._children[parent]
        self._add_to_nodes(node, parent)
        siblings.append(node)
        # Create new entry for it's own children:
        self._children[node] = []

    @observed
    def remove(self, node):
        """
        Remove @node from the tree.
        """
        # First remove children:
        children = list(self._children[node])
        for c in children:
            self.remove(c)
        # Remove from parent item
        self.get_siblings(node).remove(node)
        # Remove data entries:
        del self._children[node]
        self._nodes.remove(node)


    @observed
    def reparent(self, node, parent):
        """
        Set new parent for a node. Parent can be None.
        """
        # remove from parent
        self.get_siblings(node).remove(node)

        # add to new parent
        siblings = self._children[parent]
        self._add_to_nodes(node, parent)
        siblings.append(node)

    reversible_pair(add, remove,
                    bind1={'parent': lambda self, node: self.get_parent(node) })

    # Disable add/remove by default, since they are handled by canvas.Canvas
    disable_dispatching(add)
    disable_dispatching(remove)


# vi:sw=4:et
