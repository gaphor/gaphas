import itertools
import pytest

from gaphas.quadtree import Quadtree


@pytest.fixture()
def qtree():
    qtree: Quadtree[str, None] = Quadtree()
    for i, j in itertools.product(range(0, 100, 10), range(0, 100, 10)):
        qtree.add(item=f"{i:d}x{j:d}", bounds=(i, j, 10, 10), data=None)
    return qtree


def test_initial_size(qtree):
    assert qtree.bounds == (0, 0, 100, 100)


def test_lookups(qtree):
    for i, j in itertools.product(range(100, 10), range(100, 10)):
        assert qtree.find_intersect(rect=(i + 1, j + 1, 1, 1)) == [f"{i:d}x{j:d}"], (
            qtree.find_intersect(rect=(i + 1, j + 1, 1, 1))
        )


def test_with_rectangles(qtree):
    assert len(qtree._ids) == 100, len(qtree._ids)

    for i, j in itertools.product(range(100, 10), range(100, 10)):
        assert qtree.find_intersect(rect=(i + 1, j + 1, 1, 1)) == [f"{i:d}x{j:d}"], (
            qtree.find_intersect(rect=(i + 1, j + 1, 1, 1))
        )


def test_moving_items(qtree):
    qtree.capacity = 10
    assert len(qtree._ids) == 100, len(qtree._ids)
    assert qtree._bucket._buckets, qtree._bucket._buckets
    for i in range(4):
        assert qtree._bucket._buckets[i]._buckets
        for j in range(4):
            assert not qtree._bucket._buckets[i]._buckets[j]._buckets

    # Check contents:
    # First sub-level contains 9 items. second level contains 4 items
    # ==> 4 * (9 + (4 * 4)) = 100
    assert len(qtree._bucket.items) == 0, qtree._bucket.items
    for i in range(4):
        assert len(qtree._bucket._buckets[i].items) == 9
        for _item, bounds in qtree._bucket._buckets[i].items.items():
            assert qtree._bucket.find_bucket(bounds) is qtree._bucket._buckets[i]
        for j in range(4):
            assert len(qtree._bucket._buckets[i]._buckets[j].items) == 4

    assert qtree.get_bounds("0x0")
    # Now move item '0x0' to the center of the first quadrant (20, 20)
    qtree.add("0x0", (20, 20, 10, 10), None)
    assert len(qtree._bucket.items) == 0
    assert len(qtree._bucket._buckets[0]._buckets[0].items) == 3, (
        qtree._bucket._buckets[0]._buckets[0].items
    )
    assert len(qtree._bucket._buckets[0].items) == 10, qtree._bucket._buckets[0].items

    # Now move item '0x0' to the second quadrant (70, 20)
    qtree.add("0x0", (70, 20, 10, 10), None)
    assert len(qtree._bucket.items) == 0
    assert len(qtree._bucket._buckets[0]._buckets[0].items) == 3, (
        qtree._bucket._buckets[0]._buckets[0].items
    )
    assert len(qtree._bucket._buckets[0].items) == 9, qtree._bucket._buckets[0].items
    assert len(qtree._bucket._buckets[1].items) == 10, qtree._bucket._buckets[1].items


def test_get_data(qtree):
    """Test extra data added to a node."""
    for i, j in itertools.product(range(0, 100, 10), range(0, 100, 10)):
        qtree.add(item=f"{i:d}x{j:d}", bounds=(i, j, 10, 10), data=i + j)

    for i, j in itertools.product(range(0, 100, 10), range(0, 100, 10)):
        assert i + j == qtree.get_data(item=f"{i:d}x{j:d}")


def test_resize(qtree: Quadtree):
    qtree.add("0x0", (20, 130, 60, 60), None)

    assert "0x0" in qtree.find_inside((0, 100, 100, 200))


def test_dump_quadtree(qtree, capsys):
    qtree.dump()
    captured = capsys.readouterr()

    assert "gaphas.quadtree.QuadtreeBucket" in captured.out
