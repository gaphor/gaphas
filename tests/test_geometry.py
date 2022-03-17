from collections.abc import Iterable

import pytest

from gaphas.geometry import (
    Rectangle,
    distance_line_point,
    distance_rectangle_border_point,
    distance_rectangle_point,
    intersect_line_line,
    point_on_rectangle,
)


def test_rectangle_is_iterable():
    assert isinstance(Rectangle(), Iterable)


def test_distance_line_point():
    assert distance_line_point((0.0, 0.0), (2.0, 4.0), point=(3.0, 4.0)) == (
        1.0,
        (2.0, 4.0),
    )
    assert distance_line_point((0.0, 0.0), (2.0, 4.0), point=(-1.0, 0.0)) == (
        1.0,
        (0.0, 0.0),
    )
    assert distance_line_point((0.0, 0.0), (2.0, 4.0), point=(1.0, 2.0)) == (
        0.0,
        (1.0, 2.0),
    )


def test_distance_line_point_complex():
    d, p = distance_line_point((0.0, 0.0), (2.0, 4.0), point=(2.0, 2.0))

    assert f"{d:.3f}" == "0.894"
    assert f"({p[0]:.3f}, {p[1]:.3f})" == "(1.200, 2.400)"


@pytest.mark.parametrize(
    ["line_start", "line_end", "point"],
    [
        [(0, 0), (2, 2), (-1, 0)],
        [(0, 0), (0, 0), (-1, 0)],
        [(0, 0), (2, 2), (3, 2)],
        [(0, 0), (2, 3), (1, 1)],
    ],
)
def test_distance_line_point_does_not_return_inputs(line_start, line_end, point):
    # Rationale: inputs can be of a different type (e.g. Position)
    # but the function should always return a tuple.

    _distance, point_on_line = distance_line_point(line_start, line_end, point)

    assert point_on_line is not line_start
    assert point_on_line is not line_end
    assert point_on_line is not point


def test_distance_rectangle_point():
    assert distance_rectangle_point((2, 0, 2, 2), (0, 0)) == 2
    assert distance_rectangle_point(Rectangle(0, 0, 10, 10), (11, -1)) == 2
    assert distance_rectangle_point((0, 0, 10, 10), (11, -1)) == 2
    assert distance_rectangle_point((0, 0, 10, 10), (-1, 11)) == 2


def test_distance_point_in_rectangle():
    assert distance_rectangle_point((0, 0, 2, 2), (1, 1)) == 0


def test_distance_with_negative_numbers_in_rectangle():
    assert distance_rectangle_point((-50, -100, 100, 100), (-17, -65)) == 0


def test_distance_rectangle_border_point():
    assert distance_rectangle_border_point((2, 0, 2, 2), (0, 0)) == 2
    assert distance_rectangle_border_point(Rectangle(0, 0, 10, 10), (11, -1)) == 2
    assert distance_rectangle_border_point((0, 0, 10, 10), (11, -1)) == 2
    assert distance_rectangle_border_point((0, 0, 10, 10), (3, 4)) == -3
    assert distance_rectangle_border_point((0, 0, 2, 2), (1, 1)) == -1


def test_point_on_rectangle():
    assert point_on_rectangle((2, 2, 2, 2), (0, 0)) == (2, 2)
    assert point_on_rectangle((2, 2, 2, 2), (3, 0)) == (3, 2)
    assert point_on_rectangle(Rectangle(0, 0, 10, 10), (11, -1)) == (10, 0)
    assert point_on_rectangle((0, 0, 10, 10), (5, 12)) == (5, 10)
    assert point_on_rectangle(Rectangle(0, 0, 10, 10), (12, 5)) == (10, 5)
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (3, 4)) == (3, 4)
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (0, 3)) == (1, 3)
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (4, 3)) == (4, 3)


def test_point_on_rectangle_border():
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (4, 9), border=True) == (4, 11)
    assert point_on_rectangle((1, 1, 10, 10), (4, 6), border=True) == (1, 6)
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (5, 3), border=True) == (5, 1)
    assert point_on_rectangle(Rectangle(1, 1, 10, 10), (8, 4), border=True) == (11, 4)
    assert point_on_rectangle((1, 1, 10, 100), (5, 8), border=True) == (1, 8)
    assert point_on_rectangle((1, 1, 10, 100), (5, 98), border=True) == (5, 101)


def test_intersect_line_line():
    assert intersect_line_line((3, 0), (8, 10), (0, 0), (10, 10)) == (6.5, 6.5)
    assert intersect_line_line((0, 0), (10, 10), (3, 0), (8, 10)) == (6.5, 6.5)
    assert intersect_line_line((0, 0), (10, 10), (8, 10), (3, 0)) == (6.5, 6.5)
    assert intersect_line_line((8, 10), (3, 0), (0, 0), (10, 10)) == (6.5, 6.5)


def test_intersect_line_line_not_crossing():
    assert intersect_line_line((0, 0), (0, 10), (3, 0), (8, 10)) is None
    assert intersect_line_line((0, 0), (0, 10), (3, 0), (3, 10)) is None
