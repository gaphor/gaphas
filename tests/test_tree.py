import pytest

from gaphas.tree import Tree


@pytest.fixture()
def tree_fixture():
    """
    Return a tree

    Args:
    """
    node = ["n0", "n1", "n2", "n3", "n4", "n5", "n6", "n7"]
    return Tree(), node


def test_add(tree_fixture):
    """Test creating node trees."""
    tree = tree_fixture[0]
    n = tree_fixture[1]
    tree.add(n[1])
    assert len(tree._nodes) == 1
    assert len(tree._children) == 2
    assert len(tree._children[None]) == 1
    assert len(tree._children[n[1]]) == 0

    tree.add(n[2])
    tree.add(n[3], parent=n[1])
    assert len(tree._nodes) == 3
    assert len(tree._children) == 4
    assert len(tree._children[None]) == 2
    assert len(tree._children[n[1]]) == 1
    assert len(tree._children[n[2]]) == 0
    assert len(tree._children[n[2]]) == 0
    assert tree._nodes == [n[1], n[3], n[2]]

    tree.add(n[4], parent=n[3])
    assert tree._nodes == [n[1], n[3], n[4], n[2]]

    tree.add(n[5], parent=n[3])
    assert tree._nodes == [n[1], n[3], n[4], n[5], n[2]]

    tree.add(n[6], parent=n[2])
    assert tree._nodes == [n[1], n[3], n[4], n[5], n[2], n[6]]

    tree.add(n[7], parent=n[1])
    assert len(tree._children) == 8
    assert tree._nodes == [n[1], n[3], n[4], n[5], n[7], n[2], n[6]]
    assert tree.get_parent(n[7]) is n[1]
    assert tree.get_parent(n[6]) is n[2]
    assert tree.get_parent(n[5]) is n[3]
    assert tree.get_parent(n[4]) is n[3]
    assert tree.get_parent(n[3]) is n[1]
    assert tree.get_parent(n[2]) is None
    assert tree.get_parent(n[1]) is None


def test_add_on_index(tree_fixture):
    """
    Test if the given tree is on the given tree.

    Args:
        tree_fixture: (str): write your description
    """
    tree = tree_fixture[0]
    n = tree_fixture[1]
    tree.add(n[1])
    tree.add(n[2])
    tree.add(n[3], index=1)
    assert tree.get_children(None) == [n[1], n[3], n[2]], tree.get_children(None)
    assert tree.nodes == [n[1], n[3], n[2]], tree.nodes

    tree.add(n[4], parent=n[3])
    tree.add(n[5], parent=n[3], index=0)
    assert tree.get_children(None) == [n[1], n[3], n[2]], tree.get_children(None)
    assert tree.nodes == [n[1], n[3], n[5], n[4], n[2]], tree.nodes
    assert tree.get_children(n[3]) == [n[5], n[4]], tree.get_children(n[3])


def test_remove(tree_fixture):
    """Test removal of nodes."""
    tree = tree_fixture[0]
    n = tree_fixture[1]
    tree.add(n[1])
    tree.add(n[2])
    tree.add(n[3], parent=n[1])
    tree.add(n[4], parent=n[3])
    tree.add(n[5], parent=n[4])

    assert tree._nodes == [n[1], n[3], n[4], n[5], n[2]]

    all_ch = list(tree.get_all_children(n[1]))
    assert all_ch == [n[3], n[4], n[5]], all_ch

    tree.remove(n[4])
    assert tree._nodes == [n[1], n[3], n[2]]

    tree.remove(n[1])
    assert len(tree._children) == 2
    assert tree._children[None] == [n[2]]
    assert tree._children[n[2]] == []
    assert tree._nodes == [n[2]]


def test_siblings(tree_fixture):
    """
    Test if the siblings of the tree.

    Args:
        tree_fixture: (str): write your description
    """
    tree = tree_fixture[0]
    n = tree_fixture[1]
    tree.add(n[1])
    tree.add(n[2])
    tree.add(n[3])

    assert tree.get_next_sibling(n[1]) is n[2]
    assert tree.get_next_sibling(n[2]) is n[3]
    try:
        tree.get_next_sibling(n[3])
    except IndexError:
        pass  # Okay
    else:
        raise AssertionError(
            f"Index should be out of range, not {tree.get_next_sibling(n[3])}"
        )

    assert tree.get_previous_sibling(n[3]) is n[2]
    assert tree.get_previous_sibling(n[2]) is n[1]
    try:
        tree.get_previous_sibling(n[1])
    except IndexError:
        pass  # Okay
    else:
        raise AssertionError(
            f"Index should be out of range, not {tree.get_previous_sibling(n[1])}"
        )


def test_reparent(tree_fixture):
    """
    Perform a tree_fixture.

    Args:
        tree_fixture: (str): write your description
    """
    tree = tree_fixture[0]
    n = tree_fixture[1]
    tree.add(n[1])
    tree.add(n[2])
    tree.add(n[3])
    tree.add(n[4], parent=n[2])
    tree.add(n[5], parent=n[4])

    assert tree.nodes == [n[1], n[2], n[4], n[5], n[3]], tree.nodes

    tree.move(n[4], parent=n[1], index=0)
    assert tree.nodes == [n[1], n[4], n[5], n[2], n[3]], tree.nodes
    assert tree.get_children(n[2]) == [], tree.get_children(n[2])
    assert tree.get_children(n[1]) == [n[4]], tree.get_children(n[1])
    assert tree.get_children(n[4]) == [n[5]], tree.get_children(n[4])

    tree.move(n[4], parent=None, index=0)
    assert tree.nodes == [n[4], n[5], n[1], n[2], n[3]], tree.nodes
