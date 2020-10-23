import pytest

from gaphas.matrix import Matrix
from gaphas.position import MatrixProjection, Position
from gaphas.solver import Solver, Variable


@pytest.fixture
def solver():
    return Solver()


@pytest.mark.parametrize("position", [(0, 0), (1, 2)])
def test_position(position):
    pos = Position(position)
    assert position[0] == pos.x
    assert position[1] == pos.y


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


def test_matrix_projection_sets_handlers_just_in_time():
    pos = Position((0, 0))
    matrix = Matrix()
    proj = MatrixProjection(pos, matrix)

    def handler(c):
        pass

    assert not matrix._handlers
    assert not pos.x._handlers
    assert not pos.y._handlers

    proj.add_handler(handler)

    assert matrix._handlers
    assert pos.x._handlers
    assert pos.y._handlers

    proj.remove_handler(handler)

    assert not matrix._handlers
    assert not pos.x._handlers
    assert not pos.y._handlers
