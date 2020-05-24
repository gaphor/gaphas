import pytest

from gaphas.connector import Position, Handle
from gaphas.solver import Variable


@pytest.mark.parametrize("position", [(0, 0), (1, 2)])
def test_position(position):
    pos = Position(position)
    assert position[0] == pos.x
    assert position[1] == pos.y


def test_handle_x_y():
    h = Handle()
    assert 0.0 == h.pos.x
    assert 0.0 == h.pos.y
