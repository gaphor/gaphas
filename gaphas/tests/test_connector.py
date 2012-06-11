
import unittest
from gaphas.connector import Position, Handle
from gaphas.solver import Variable

class PositionTestCase(unittest.TestCase):

    def test_position(self):
        pos = Position((0, 0))
        self.assertEquals(0, pos.x)
        self.assertEquals(0, pos.y)

    def test_position(self):
        pos = Position((1, 2))
        self.assertEquals(1, pos.x)
        self.assertEquals(2, pos.y)

    def test_set_xy(self):
        pos = Position((1,2))
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
        self.assertEquals(0.0, h.x)
        self.assertEquals(0.0, h.y)
        
# vim: sw=4:et:ai
