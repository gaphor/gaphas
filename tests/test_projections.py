import pytest

from gaphas.connector import Position
from gaphas.matrix import Matrix
from gaphas.projections import MatrixProjection
from gaphas.solver import Variable


def test_matrix_projection_exposes_variables():
    proj = MatrixProjection(Position((0, 0)), Matrix())

    assert isinstance(proj.x, Variable)
    assert isinstance(proj.y, Variable)


@pytest.mark.parametrize(
    "position,matrix,result",
    [
        [(0, 0), (1, 0, 0, 1, 0, 0), (0, 0)],
        [(2, 4), (2, 0, 0, 1, 2, 3), (6, 7)],
        [(2, 4), (2, 0, 0, 1, 2, 3), (6, 7)],
    ],
)
def test_position_is_projected(position, matrix, result):
    pos = Position(position)
    m = Matrix(*matrix)
    proj = MatrixProjection(pos, m)

    assert proj.x == result[0]
    assert proj.y == result[1]


@pytest.mark.parametrize(
    "position,matrix,result",
    [
        [(2, 0), (1, 0, 0, 1, 0, 0), (2, 0)],
        [(2, 0), (1, 0, 0, 1, 4, 3), (-2, -3)],
        [(1, 2), (1, 0, 0, 1, 4, 3), (-3, -1)],
    ],
)
def test_projection_updates_original(position, matrix, result):
    pos = Position((0, 0))
    m = Matrix(*matrix)

    proj = MatrixProjection(pos, m)
    proj.x, proj.y = position

    assert pos.x == result[0]
    assert pos.y == result[1]
