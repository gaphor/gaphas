"""
Simple class containing the tree structure for the canvas items.

"""

__version__ = "$Revision$"
# $HeadURL$


class Tree(object):
    """A Tree structure.
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
        """Return the parent item of @node.
        """
        for item, children in self._children.items():
            if node in children:
                return item

    def get_children(self, node):
        """Return all child objects of @node.
        """
        return self._children[node]

    def get_siblings(self, node):
        """Get all siblings of @node, including @node.
        """
        parent = self.get_parent(node)
        return self._children[parent] #[ n for n in self._children[parent] if not n is node ]

    def get_next_sibling(self, node):
        """Return the node on the same level after @node.
        """
        parent = self.get_parent(node)
        siblings = self._children[parent]
        return siblings[siblings.index(node) + 1]

    def get_previous_sibling(self, node):
        """Return the node on the same level before @node.
        """
        parent = self.get_parent(node)
        siblings = self._children[parent]
        return siblings[siblings.index(node) - 1]

    def get_ancestors(self, node):
        """Iterate all parents and parents of parents, etc.
        """
        parent = self.get_parent(node)
        while parent:
            yield parent
            parent = self.get_parent(parent)

    def _add_to_nodes(self, node, parent):
        """Called only from add()
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

    def add(self, node, parent=None):
        """Add @node to the tree. @parent is the parent node, which may
        be None if the item should be added to the root item.
        """
        assert not self._children.get(node)
        siblings = self._children[parent]
        self._add_to_nodes(node, parent)
        siblings.append(node)
        # Create new entry for it's own children:
        self._children[node] = []

    def remove(self, node):
        """Remove @node from the tree.
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


def test_add():
    """Test creating node trees.
    """
    print 'test_add'

    tree = Tree()
    n1 = 'n1'
    n2 = 'n2'
    n3 = 'n3'

    tree.add(n1)
    assert len(tree._nodes) == 1
    assert len(tree._children) == 2
    assert len(tree._children[None]) == 1
    assert len(tree._children[n1]) == 0

    tree.add(n2)
    tree.add(n3, parent=n1)
    assert len(tree._nodes) == 3
    assert len(tree._children) == 4
    assert len(tree._children[None]) == 2
    assert len(tree._children[n1]) == 1
    assert len(tree._children[n2]) == 0
    assert len(tree._children[n2]) == 0
    print tree._nodes
    assert tree._nodes == [n1, n3, n2]

    n4 = 'n4'
    tree.add(n4, parent=n3)
    print tree._nodes
    assert tree._nodes == [n1, n3, n4, n2]

    n5 = 'n5'
    tree.add(n5, parent=n3)
    print tree._nodes
    assert tree._nodes == [n1, n3, n4, n5, n2]

    n6 = 'n6'
    tree.add(n6, parent=n2)
    print tree._nodes
    assert tree._nodes == [n1, n3, n4, n5, n2, n6]

    n7 = 'n7'
    tree.add(n7, parent=n1)
    print tree._nodes
    assert len(tree._children) == 8
    assert tree._nodes == [n1, n3, n4, n5, n7, n2, n6]
    assert tree.get_parent(n7) is n1
    assert tree.get_parent(n6) is n2
    assert tree.get_parent(n5) is n3
    assert tree.get_parent(n4) is n3
    assert tree.get_parent(n3) is n1
    assert tree.get_parent(n2) is None
    assert tree.get_parent(n1) is None

def test_remove():
    """Test removal of nodes.
    """
    print 'test_remove'

    tree = Tree()
    n1 = 'n1'
    n2 = 'n2'
    n3 = 'n3'
    n4 = 'n4'
    n5 = 'n5'

    tree.add(n1)
    tree.add(n2)
    tree.add(n3, parent=n1)
    tree.add(n4, parent=n3)
    tree.add(n5, parent=n4)

    assert tree._nodes == [n1, n3, n4, n5, n2]

    tree.remove(n4)
    assert tree._nodes == [n1, n3, n2]

    tree.remove(n1)
    assert len(tree._children) == 2
    assert tree._children[None] == [n2]
    assert tree._children[n2] == []
    assert tree._nodes == [n2]


if __name__ == '__main__':
    test_add()
    test_remove()
