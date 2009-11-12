
import unittest
from gaphas.connector import Position, Handle

class PositionTestCase(unittest.TestCase):

    def test_position(self):
        pos = Position((0, 0))
        self.assertEquals(0, pos.x)
        self.assertEquals(0, pos.y)

    def test_position(self):
        pos = Position((1, 2))
        self.assertEquals(1, pos.x)
        self.assertEquals(2, pos.y)


class HandleTestCase(unittest.TestCase):

    def test_handle_x_y(self):
        h = Handle()
        self.assertEquals(0.0, h.x)
        self.assertEquals(0.0, h.y)
        
# vim: sw=4:et:ai
