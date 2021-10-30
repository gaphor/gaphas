from gaphas.collision import colliding_lines, manhattan_distance, route, turns_in_path
from gaphas.connections import Connections
from gaphas.item import Element, Item, Line
from gaphas.quadtree import Quadtree


def test_colliding_lines():
    connections = Connections()
    qtree: Quadtree[Item, None] = Quadtree()

    line = Line(connections=connections)
    line.head.pos = (0, 50)
    line.tail.pos = (200, 50)

    element = Element(connections=connections)
    element.height = 100
    element.width = 100
    element.matrix.translate(50, 0)

    qtree.add(line, (0, 50, 200, 50))
    qtree.add(element, (50, 0, 150, 100))

    collisions = list(colliding_lines(qtree))

    assert (line, element) in collisions


def test_maze():

    _maze = [
        [(0), 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, (0), 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]

    start = (0, 0)
    end = (7, 6)

    def weight(x, y, _current_node):
        return (
            1
            if 0 <= x < len(_maze) and 0 <= y < len(_maze[x]) and not _maze[y][x]
            else 10
        )

    path_and_dir = route(start, end, weight=weight, heuristic=manhattan_distance(*end))
    dump_maze(_maze, [pd[0] for pd in path_and_dir])
    assert path_and_dir == [
        ((0, 0), (0, 0)),
        ((1, 1), (1, 1)),
        ((2, 2), (1, 1)),
        ((3, 3), (1, 1)),
        ((3, 4), (0, 1)),
        ((4, 5), (1, 1)),
        ((5, 6), (1, 1)),
        ((6, 6), (1, 0)),
        ((7, 6), (1, 0)),
    ], path_and_dir


def test_unsolvable_maze():

    start = (0, 0)
    end = (3, 3)

    def weight(x, y, _current_node):
        wall = y == 2
        return 1 if 0 <= x < 4 and 0 <= y < 4 and not wall else "inf"

    path = route(start, end, weight=weight)
    assert path == [], path


def dump_maze(maze, path):
    for y, row in enumerate(maze):
        for x, v in enumerate(row):
            if (x, y) == path[0]:
                p = "S"
            elif (x, y) == path[-1]:
                p = "E"
            elif (x, y) in path:
                p = "x"
            else:
                p = v
            print(p, end=" ")
        print()


def test_find_turns_in_path():
    path_and_dir = [
        ((0, 0), (0, 0)),
        ((1, 1), (1, 1)),
        ((2, 2), (1, 1)),
        ((3, 3), (1, 1)),
        ((3, 4), (0, 1)),
        ((4, 5), (1, 1)),
        ((5, 6), (1, 1)),
        ((6, 6), (1, 0)),
        ((7, 6), (1, 0)),
    ]

    expected_path = [(0, 0), (3, 3), (3, 4), (5, 6), (7, 6)]
    assert list(turns_in_path(path_and_dir)) == expected_path


def test_find_turns_in_empty_path():
    assert list(turns_in_path([])) == []
