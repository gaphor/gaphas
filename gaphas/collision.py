"""Collision avoiding.

Reroute lines when they cross elements and other lines.
"""

from typing import Iterable

from gaphas.geometry import intersect_rectangle_line
from gaphas.item import Item, Line
from gaphas.quadtree import Quadtree


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
