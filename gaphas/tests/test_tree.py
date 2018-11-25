import unittest
from gaphas.tree import Tree


class TreeTestCase(unittest.TestCase):
    def test_add(self):
        """
        Test creating node trees.
        """
        tree = Tree()
        n1 = "n1"
        n2 = "n2"
        n3 = "n3"

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
        assert tree._nodes == [n1, n3, n2]

        n4 = "n4"
        tree.add(n4, parent=n3)
        assert tree._nodes == [n1, n3, n4, n2]

        n5 = "n5"
        tree.add(n5, parent=n3)
        assert tree._nodes == [n1, n3, n4, n5, n2]

        n6 = "n6"
        tree.add(n6, parent=n2)
        assert tree._nodes == [n1, n3, n4, n5, n2, n6]

        n7 = "n7"
        tree.add(n7, parent=n1)
        assert len(tree._children) == 8
        assert tree._nodes == [n1, n3, n4, n5, n7, n2, n6]
        assert tree.get_parent(n7) is n1
        assert tree.get_parent(n6) is n2
        assert tree.get_parent(n5) is n3
        assert tree.get_parent(n4) is n3
        assert tree.get_parent(n3) is n1
        assert tree.get_parent(n2) is None
        assert tree.get_parent(n1) is None

    def test_add_on_index(self):
        tree = Tree()
        n1 = "n1"
        n2 = "n2"
        n3 = "n3"
        n4 = "n4"
        n5 = "n5"

        tree.add(n1)
        tree.add(n2)
        tree.add(n3, index=1)
        assert tree.get_children(None) == [n1, n3, n2], tree.get_children(None)
        assert tree.nodes == [n1, n3, n2], tree.nodes

        tree.add(n4, parent=n3)
        tree.add(n5, parent=n3, index=0)
        assert tree.get_children(None) == [n1, n3, n2], tree.get_children(None)
        assert tree.nodes == [n1, n3, n5, n4, n2], tree.nodes
        assert tree.get_children(n3) == [n5, n4], tree.get_children(n3)

    def test_remove(self):
        """
        Test removal of nodes.
        """
        tree = Tree()
        n1 = "n1"
        n2 = "n2"
        n3 = "n3"
        n4 = "n4"
        n5 = "n5"

        tree.add(n1)
        tree.add(n2)
        tree.add(n3, parent=n1)
        tree.add(n4, parent=n3)
        tree.add(n5, parent=n4)

        assert tree._nodes == [n1, n3, n4, n5, n2]

        all_ch = list(tree.get_all_children(n1))
        assert all_ch == [n3, n4, n5], all_ch

        tree.remove(n4)
        assert tree._nodes == [n1, n3, n2]

        tree.remove(n1)
        assert len(tree._children) == 2
        assert tree._children[None] == [n2]
        assert tree._children[n2] == []
        assert tree._nodes == [n2]

    def test_siblings(self):
        tree = Tree()
        n1 = "n1"
        n2 = "n2"
        n3 = "n3"

        tree.add(n1)
        tree.add(n2)
        tree.add(n3)

        assert tree.get_next_sibling(n1) is n2
        assert tree.get_next_sibling(n2) is n3
        try:
            tree.get_next_sibling(n3)
        except IndexError:
            pass  # okay
        else:
            raise AssertionError(
                "Index should be out of range, not %s" % tree.get_next_sibling(n3)
            )

        assert tree.get_previous_sibling(n3) is n2
        assert tree.get_previous_sibling(n2) is n1
        try:
            tree.get_previous_sibling(n1)
        except IndexError:
            pass  # okay
        else:
            raise AssertionError(
                "Index should be out of range, not %s" % tree.get_previous_sibling(n1)
            )

    def test_reparent(self):
        tree = Tree()
        n1 = "n1"
        n2 = "n2"
        n3 = "n3"
        n4 = "n4"
        n5 = "n5"

        tree.add(n1)
        tree.add(n2)
        tree.add(n3)
        tree.add(n4, parent=n2)
        tree.add(n5, parent=n4)

        assert tree.nodes == [n1, n2, n4, n5, n3], tree.nodes

        tree.reparent(n4, parent=n1, index=0)
        assert tree.nodes == [n1, n4, n5, n2, n3], tree.nodes
        assert tree.get_children(n2) == [], tree.get_children(n2)
        assert tree.get_children(n1) == [n4], tree.get_children(n1)
        assert tree.get_children(n4) == [n5], tree.get_children(n4)

        tree.reparent(n4, parent=None, index=0)
        assert tree.nodes == [n4, n5, n1, n2, n3], tree.nodes


# vi:sw=4:et:ai
