import pytest

from gaphas.geometry import (
    distance_line_point,
    distance_rectangle_point,
    intersect_line_line,
    point_on_rectangle,
)


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


def test_distance_point_in_rectangle():
    assert distance_rectangle_point((0, 0, 2, 2), (1, 1)) == 0


def test_distance_with_negative_numbers_in_rectangle():
    assert distance_rectangle_point((-50, -100, 100, 100), (-17, -65)) == 0


def test_point_on_rectangle():
    assert point_on_rectangle((2, 2, 2, 2), (0, 0)) == (2, 2)
    assert point_on_rectangle((2, 2, 2, 2), (3, 0)) == (3, 2)


def test_intersect_line_line():
    assert intersect_line_line((3, 0), (8, 10), (0, 0), (10, 10)) == (6, 6)
    assert intersect_line_line((0, 0), (10, 10), (3, 0), (8, 10)) == (6, 6)
    assert intersect_line_line((0, 0), (10, 10), (8, 10), (3, 0)) == (6, 6)
    assert intersect_line_line((8, 10), (3, 0), (0, 0), (10, 10)) == (6, 6)


def test_intersect_line_line_not_crossing():
    assert intersect_line_line((0, 0), (0, 10), (3, 0), (8, 10)) is None
    assert intersect_line_line((0, 0), (0, 10), (3, 0), (3, 10)) is None
