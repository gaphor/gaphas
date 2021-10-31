"""Collision avoiding.

Reroute lines when they cross elements and other lines.

Limitations:

- can only deal with normal lines (not orthogonal)
- uses bounding box for grid occupancy (for element and line!)
"""

from __future__ import annotations

from itertools import groupby
from operator import attrgetter, itemgetter
from typing import Callable, Iterable, Literal, NamedTuple, Tuple, Union

from gaphas.geometry import intersect_rectangle_line
from gaphas.item import Item, Line
from gaphas.quadtree import Quadtree
from gaphas.segment import Segment
from gaphas.view.model import Model

Pos = Tuple[int, int]


class Node(NamedTuple):
    parent: object | None  # type should be Node
    position: Pos
    direction: Pos
    g: int
    f: int


Walker = Callable[[int, int], bool]
Heuristic = Callable[[int, int], int]
Weight = Callable[[int, int, Node], Union[int, Literal["inf"]]]


def colliding_lines(qtree: Quadtree) -> Iterable[tuple[Line, Item]]:
    lines = (
        item for item in qtree.items if isinstance(item, Line) and not item.orthogonal
    )
    for line in lines:
        items = qtree.find_intersect(qtree.get_bounds(line))
        if not items:
            continue

        segments = [
            (
                line.matrix_i2c.transform_point(*start),
                line.matrix_i2c.transform_point(*end),
            )
            for start, end in line.segments
        ]
        for item in items:
            if item is line:
                continue
            bounds = qtree.get_bounds(item)
            for seg_start, seg_end in segments:
                if intersect_rectangle_line(bounds, seg_end, seg_start):
                    yield (line, item)
                    break


def update_colliding_lines(model: Model, qtree: Quadtree, grid_size: int = 20) -> None:
    for line, _item in colliding_lines(qtree):
        # find start and end pos in terms of the grid
        matrix = line.matrix_i2c
        start_x, start_y = (
            int(v / grid_size) for v in matrix.transform_point(*line.head.pos)
        )
        end_x, end_y = (
            int(v / grid_size) for v in matrix.transform_point(*line.tail.pos)
        )
        excluded_items: set[Item] = {line}

        def weight(x, y, current_node):
            direction_penalty = 0 if same_direction(x, y, current_node) else 2
            occupied_penalty = (
                5 if tile_occupied(x, y, grid_size, qtree, excluded_items) else 0
            )
            return 1 + direction_penalty + occupied_penalty

        path_with_direction = route(
            (start_x, start_y),
            (end_x, end_y),
            weight=weight,
            heuristic=manhattan_distance(end_x, end_y),
        )
        path = list(turns_in_path(path_with_direction))

        segment = Segment(line, model)
        while len(path) > len(line.handles()):
            segment.split_segment(0)
        while len(path) < len(line.handles()):
            segment.merge_segment(0)

        matrix.invert()
        for pos, handle in zip(path[1:-1], line.handles()[1:-1]):
            cx = pos[0] * grid_size + grid_size / 2
            cy = pos[1] * grid_size + grid_size / 2
            handle.pos = matrix.transform_point(cx, cy)

        model.request_update(line)


def same_direction(x: int, y: int, node: Node) -> bool:
    node_pos = node.position
    dir_x = x - node_pos[0]
    dir_y = y - node_pos[1]
    node_dir = node.direction
    return dir_x == node_dir[0] and dir_y == node_dir[1]


def tile_occupied(
    x: int, y: int, grid_size: int, qtree: Quadtree, excluded_items: set[Item]
) -> bool:
    items = (
        qtree.find_intersect((x * grid_size, y * grid_size, grid_size, grid_size))
        - excluded_items
    )
    return bool(items)


def turns_in_path(path_and_dir: list[tuple[Pos, Pos]]) -> Iterable[Pos]:
    for _, group in groupby(path_and_dir, key=itemgetter(1)):
        *_, (position, _) = group
        yield position


# Heuristics:


def constant_heuristic(cost):
    def heuristic(_x, _y):
        return cost

    return heuristic


def manhattan_distance(end_x, end_y):
    def heuristic(x, y):
        return abs(x - end_x) + abs(y - end_y)

    return heuristic


def quadratic_distance(end_x, end_y):
    def heuristic(x, y):
        return ((x - end_x) ** 2) + ((y - end_y) ** 2)

    return heuristic


def route(
    start: Pos,
    end: Pos,
    weight: Weight,
    heuristic: Heuristic = constant_heuristic(1),
) -> list[tuple[Pos, Pos]]:
    """Simple A* router/solver.

    This solver is tailored towards grids (mazes).

    Args:
        start: Start position
        end: Final position
        weight:
            Provide a cost for the move to the new position (x, y). Weight can be "inf"
            to point out you can never move there. Weight can consist of many parts:
            a weight of travel (normally 1), but also a cost for bending, for example.
        heuristic:
            An (optimistic) estimate of how long it would take to reach `end` from the
            position (x, y). Normally this is some distance (manhattan or quadratic).
            Default is a constant distance (1), which would make it a standard shortest
            path algorithm a la Dijkstra.

    Returns:
        A list of the shortest path found in tuples (position, direction), or [].
    """
    open_nodes = [Node(None, start, (0, 0), 0, 0)]
    closed_positions = set()

    f = attrgetter("f")
    directions = [
        (0, -1),
        (0, 1),
        (-1, 0),
        (1, 0),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]

    while open_nodes:
        current_node = min(open_nodes, key=f)

        if current_node.position == end:
            return reconstruct_path(current_node)

        for direction in directions:
            node_x = current_node.position[0] + direction[0]
            node_y = current_node.position[1] + direction[1]

            w = weight(node_x, node_y, current_node)
            if w == "inf":
                continue

            node_position = (node_x, node_y)

            if node_position in closed_positions:
                continue

            g = current_node.g + w

            for open_node in open_nodes:
                if node_position == open_node.position and g > open_node.g:
                    continue

            open_nodes.append(
                Node(
                    current_node,
                    node_position,
                    direction,
                    g,
                    g + heuristic(node_x, node_y),
                )
            )

        open_nodes.remove(current_node)
        closed_positions.add(current_node.position)

    return []


def reconstruct_path(node: Node) -> list[tuple[Pos, Pos]]:
    path = []
    current = node
    while current:
        path.append((current.position, current.direction))
        current = current.parent  # type: ignore[assignment]
    return path[::-1]
