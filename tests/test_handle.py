from gaphas.connector import Handle


def test_handle_x_y():
    h = Handle()
    assert 0.0 == h.pos.x
    assert 0.0 == h.pos.y
