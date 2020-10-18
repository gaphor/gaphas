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
def test_projection_updates_when_original_is_changed(solver, position, matrix, result):
    pos = Position((0, 0))
    proj = MatrixProjection(pos, matrix)
    solver.add_constraint(proj)
    solver.solve()

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
def test_original_updates_when_projection_is_changed(solver, position, matrix, result):
    pos = Position((0, 0))
    proj = MatrixProjection(pos, matrix)
    solver.add_constraint(proj)
    solver.solve()

    proj.x, proj.y = position

    solver.solve()

    print(pos)
    print(proj.x, proj.y)
    assert pos.x == result[0]
    assert pos.y == result[1]


def test_projection_updates_when_matrix_is_changed(solver):
    pos = Position((0, 0))
    matrix = Matrix()
    proj = MatrixProjection(pos, matrix)
    solver.add_constraint(proj)
    solver.solve()

    matrix.translate(2, 3)
    solver.solve()

    assert proj.x == 2
    assert proj.y == 3
