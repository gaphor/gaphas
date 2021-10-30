"""Collision avoiding.

Reroute lines when they cross elements and other lines.
"""
from __future__ import annotations

from operator import attrgetter
from typing import Callable, Iterable, Literal, NamedTuple, Tuple, Union

from gaphas.geometry import intersect_rectangle_line
from gaphas.item import Item, Line
from gaphas.quadtree import Quadtree
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
    lines = (item for item in qtree.items if isinstance(item, Line))
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


def update_colliding_lines(canvas: Model, qtree: Quadtree, grid_size: int = 20) -> None:
    for line, item in colliding_lines(qtree):
        # find start and end pos in terms of the grid
        start_x = int(line.head.pos.x / grid_size)
        start_y = int(line.head.pos.y / grid_size)
        end_x = int(line.tail.pos.x / grid_size)
        end_y = int(line.tail.pos.y / grid_size)

        def weight(x, y, current_node):
            return 1

        full_path = route(
            (start_x, start_y),
            (end_x, end_y),
            weight=weight,
            heuristic=manhattan_distance(end_x, end_y),
        )
        full_path
        # when moving items, do not update selected items
        # when moving a handle, selected items can be rerouted
        # reduce path: find corner points to put handles
        # update handles on line with new points
        canvas.request_update(line)


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


# Weight:


def constant_weight(_node_x, _node_y, _node, cost=1):
    return cost


def prefer_orthogonal(node_x, node_y, node, cost=5):
    return 1 if node_x[0] == node.position[0] or node_y[1] == node.position[1] else cost


def route(
    start: Pos,
    end: Pos,
    weight: Weight,
    heuristic: Heuristic = constant_heuristic(1),
) -> list[Pos] | None:
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
        A list of the shortest path found, or None.
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

        for dir_x, dir_y in directions:
            node_x = current_node.position[0] + dir_x
            node_y = current_node.position[1] + dir_y

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
                    (dir_x, dir_y),
                    g,
                    g + heuristic(node_x, node_y),
                )
            )

        open_nodes.remove(current_node)
        closed_positions.add(current_node.position)

    return None


def reconstruct_path(node: Node) -> list[Pos]:
    path = []
    current = node
    while current:
        path.append(current.position)  # Add direction
        current = current.parent  # type: ignore[assignment]
    return path[::-1]
