"""Simple example items.
These items are used in various tests.
"""

from item import Handle, Item
from solver import solvable

[ NW,
  NE,
  SW,
  SE ] = xrange(4)

class Box(Item):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Box, self).__init__()
        self._handles = [Handle(0, 0), Handle(width, 0),
                         Handle(0, height), Handle(width, height)]
        self._constraints = []

    def _set_width(self, width):
        """
        >>> b=Box()
        >>> b.width = 20
        >>> b.width
        20.0
        >>> b._handles[NW].x
        Variable(0, 20)
        >>> b._handles[NE].x
        Variable(20, 20)
        """
        h = self._handles
        h[NE].x = h[NW].x + width

    def _get_width(self):
        h = self._handles
        return float(h[NE].x) - float(h[NW].x)

    width = property(_get_width, _set_width)

    def _set_height(self, height):
        """
        >>> b=Box()
        >>> b.height = 20
        >>> b.height
        20.0
        >>> b._handles[NW].y
        Variable(0, 20)
        >>> b._handles[SW].y
        Variable(20, 20)
        """
        h = self._handles
        h[SW].y = h[NW].y + height

    def _get_height(self):
        h = self._handles
        return float(h[SW].y) - float(h[NW].y)

    height = property(_get_height, _set_height)

    def _set_canvas(self, canvas):
        print 'box canvas'
        if self.canvasio:
            self.teardown_constraints()
        super(Box, self)._set_canvas(canvas)
        if self.canvas:
            self.setup_constraints()

    def setup_canvas(self):
        """
        >>> from canvas import Canvas
        >>> c=Canvas()
        >>> c.solver._constraints
        {}
        >>> b = Box()
        >>> c.add(b)
        >>> b.canvas is c
        True
        >>> len(c.solver._constraints)
        4
        """
        def equal(a,b): a - b
        h=self._handles
        self._constraints = [
            self.canvas.solver.add_constraint(equal, a=h[NW].y, b=h[NE].y),
            self.canvas.solver.add_constraint(equal, a=h[SW].y, b=h[SE].y),
            self.canvas.solver.add_constraint(equal, a=h[NW].x, b=h[SW].x),
            self.canvas.solver.add_constraint(equal, a=h[NE].x, b=h[SE].x)
            ]

    def teardown_canvas(self):
        for c in self._constraints:
            self.canvas.solver.remove(c)

    def handles(self):
        return iter(self._handles)

    def update(self, context):
        pass

    def draw(self, context):
        #print 'Box.draw', self
        c = context.cairo
        c.rectangle(0,0, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(.8,.8,1, 1)
        else:
            c.set_source_rgba(1,1,1, 1)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()
        context.draw_children()

    def point(self, context, x, y):
        if 0.0 < x < float(self.width) and 0.0 < y < float(self.height):
            return 0
        else:
            return 100

class Text(Item):
    def __init__(self):
        super(Text, self).__init__()


    def draw(self, context):
        #print 'Text.draw', self
        c = context.cairo
        c.show_text('Hello')
        context.draw_children()

    def point(self, context, x, y):
        return 0

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
