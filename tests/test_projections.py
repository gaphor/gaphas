import pytest

from gaphas.connector import Position
from gaphas.matrix import Matrix
from gaphas.projections import MatrixProjection
from gaphas.solver import Solver, Variable


@pytest.fixture
def solver():
    return Solver()


def test_matrix_projection_exposes_variables():
    proj = MatrixProjection(Position((0, 0)), Matrix())

    assert isinstance(proj.x, Variable)
    assert isinstance(proj.y, Variable)


@pytest.mark.parametrize(
    "position,matrix,result",
    [
        [(0, 0), Matrix(1, 0, 0, 1, 0, 0), (0, 0)],
        [(2, 4), Matrix(2, 0, 0, 1, 2, 3), (6, 7)],
        [(2, 4), Matrix(2, 0, 0, 1, 2, 3), (6, 7)],
    ],
)
def test_position_is_projected(solver, position, matrix, result):
    pos = Position((0, 0))
    proj = MatrixProjection(pos, matrix)
    solver.add_constraint(proj)

    pos.x, pos.y = position
    solver.solve()

    assert proj.x == result[0]
    assert proj.y == result[1]


@pytest.mark.parametrize(
    "position,matrix,result",
    [
        [(0, 0), Matrix(1, 0, 0, 1, 0, 0), (0, 0)],
        [(2, 0), Matrix(1, 0, 0, 1, 0, 0), (2, 0)],
        [(2, 0), Matrix(1, 0, 0, 1, 4, 3), (-2, -3)],
        [(1, 2), Matrix(1, 0, 0, 1, 4, 3), (-3, -1)],
    ],
)
def test_projection_updates_original(solver, position, matrix, result):
    pos = Position((0, 0))

    proj = MatrixProjection(pos, matrix)
    solver.add_constraint(proj)

    proj.x, proj.y = position

    solver.solve()

    print(pos)
    print(proj.x, proj.y)
    assert pos.x == result[0]
    assert pos.y == result[1]
