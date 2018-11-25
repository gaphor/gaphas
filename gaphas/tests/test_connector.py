import unittest
from gaphas.connector import Position, Handle
from gaphas.solver import Variable


class PositionTestCase(unittest.TestCase):
    def test_position(self):
        pos = Position((0, 0))
        self.assertEqual(0, pos.x)
        self.assertEqual(0, pos.y)

    def test_position(self):
        pos = Position((1, 2))
        self.assertEqual(1, pos.x)
        self.assertEqual(2, pos.y)

    def test_set_xy(self):
        pos = Position((1, 2))
        x = Variable()
        y = Variable()
        assert x is not pos.x
        assert y is not pos.y

        pos.set_x(x)
        pos.set_y(y)
        assert x is pos.x
        assert y is pos.y


class HandleTestCase(unittest.TestCase):
    def test_handle_x_y(self):
        h = Handle()
        self.assertEqual(0.0, h.x)
        self.assertEqual(0.0, h.y)


# vim: sw=4:et:ai
