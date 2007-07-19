from gaphas.solver import Variable
from gaphas.constraint import Projector


###
### projection example
###

class AffineProjector(Projector):
    """
    Project Vector/Rectangle information from affine to common space, i.e.
     - rectangle is converted into two points representation, i.e.

        Rectangle(5, 5, 20, 20) -> (5, 5), (25, 25)

     - vector AB is converted from bound to free representation, i.e.

        Vector(5, 50, 5, -25) -> A=(5, 50), B=(10, 25)
    """
    def _cproj(self, c, *args, **kw):
        data = kw['data']
        for v in c.variables():
            v0 = data[v]
            v._value = v._value + v0


    def _iproj(self, c, *args, **kw):
        data = kw['data']
        for v in c.variables():
            v0 = data[v]
            v._value = v._value - v0



class Rectangle(object):
    """
    Rectangle defined by position (x0, y0) and size.
    """
    def __init__(self, x0, y0, width, height):
        self.x0 = Variable(x0)
        self.y0 = Variable(y0)
        self.width = Variable(width)
        self.height = Variable(height)



class Vector(object):
    """
    Vector AB, where A=(0, 0) and B=(x, y).
    """
    def __init__(self, x0, y0, x, y):
        self.x0 = Variable(x0)
        self.y0 = Variable(y0)
        self.x = Variable(x)
        self.y = Variable(y)


###
### end of projection example
###

