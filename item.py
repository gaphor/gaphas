""" Item and Handle.
"""

from geometry import Matrix
from solver import solvable

class Handle(object):
    """Handles are used to support modifications of Items.
    """

    x = solvable()
    y = solvable()

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        # Flags.. can't have enough of those
        self._connectable = True
        self._movable = True
        self._visible = True

    def _set_pos(self, pos):
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

#    def update(self, context):
#        """Update the handle. @context has the following attributes:
#         - item: the owning item
#         - matrix_i2w: Item to World transformation matrix
#        """
#        pass


class Item(object):

    def __init__(self):
        self._canvas = None
        self._matrix = Matrix()

    def _set_canvas(self, canvas):
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    def _del_canvas(self):
        self._canvas = None

    canvas = property(lambda s: s._canvas, _set_canvas, _del_canvas)

    def setup_canvas(self):
        pass

    def teardown_canvas(self):
        pass

    def _set_matrix(self, matrix):
        if not isinstance(matrix, Matrix):
            matrix = Matrix(*matrix)
        self._matrix = matrix

    matrix = property(lambda s: s._matrix, _set_matrix)

    def request_update(self):
        if self._canvas:
            self._canvas.request_update(self)

    def pre_update(self, context):
        """Do small things that have to be done before the "real" update.
        Context has the following attributes:
         - canvas: the owning canvas
         - matrix_i2w: Item to World transformation matrix
         - ... (do I need something for text processing?)
        """
        pass


    def update(self, context):
        """Like pre_update(), but this is step 2.
        """
        pass

    def draw(self, context):
        """Render the item to a canvas view.
        Context contains the following attributes:
         - matrix_i2w: Item to World transformation matrix (no need to)
         - cairo: the Cairo Context use this one to draw.
	 - view: the view that is to be rendered to
	 - selected, focused, hovered: view state of items.
        """
        pass

    def handles(self):
        """Return an iterator for the handles owned by the item.
        """
        return iter([])

    def point(self, context, x, y):
        """Get the distance from a point (@x, @y) to the item.
	@x and @y are in item coordinates.
        Context contains the following attributes:
         - matrix_i2w: Item to World transformation matrix (no need to)
         - cairo: the Cairo Context use this one to draw.
	"""
	pass



from solver import solvable

[ NW,
  NE,
  SW,
  SE ] = xrange(4)

class Element(Item):
    """ An Element has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Element, self).__init__()
        #self._handles = [Handle(0, 0), Handle(width, 0),
        #                 Handle(0, height), Handle(width, height)]
        self._handles = [ h() for h in [Handle]*4 ]
        self._constraints = []
        self.width = width
        self.height = height

    def _set_width(self, width):
        """
        >>> b=Element()
        >>> b.width = 20
        >>> b.width
        20.0
        >>> b._handles[NW].x
        Variable(0, 20)
        >>> b._handles[SE].x
        Variable(20, 20)
        """
        h = self._handles
        h[SE].x = h[NW].x + width

    def _get_width(self):
        h = self._handles
        return float(h[SE].x) - float(h[NW].x)

    width = property(_get_width, _set_width)

    def _set_height(self, height):
        """
        >>> b=Element()
        >>> b.height = 20
        >>> b.height
        20.0
        >>> b._handles[NW].y
        Variable(0, 20)
        >>> b._handles[SE].y
        Variable(20, 20)
        """
        h = self._handles
        h[SE].y = h[NW].y + height

    def _get_height(self):
        h = self._handles
        return float(h[SE].y) - float(h[NW].y)

    height = property(_get_height, _set_height)

    def setup_canvas(self):
        """
        >>> from canvas import Canvas
        >>> c=Canvas()
        >>> c.solver._constraints
        {}
        >>> b = Element()
        >>> c.add(b)
        >>> b.canvas is c
        True
        >>> len(c.solver._constraints)
        4
        >>> len(c.solver._marked_cons)
        4
        >>> c.solver.solve()
        >>> len(c.solver._constraints)
        4
        >>> len(c.solver._marked_cons)
        0
        >>> b._handles[SE].pos = (25,30)
        >>> len(c.solver._marked_cons)
        2
        >>> c.solver.solve()
        >>> float(b._handles[NE].x)
        25.0
        >>> float(b._handles[SW].y)
        30.0
        """
        def equal(a,b): return a - b
        h=self._handles
        self._constraints = [
            self.canvas.solver.add_constraint(equal, a=h[NW].y, b=h[NE].y),
            self.canvas.solver.add_constraint(equal, a=h[SW].y, b=h[SE].y),
            self.canvas.solver.add_constraint(equal, a=h[NW].x, b=h[SW].x),
            self.canvas.solver.add_constraint(equal, a=h[NE].x, b=h[SE].x)
            ]
        self.canvas.solver.mark_dirty(h[NW].x)
        self.canvas.solver.mark_dirty(h[NW].y)
        self.canvas.solver.mark_dirty(h[SE].x)
        self.canvas.solver.mark_dirty(h[SE].y)
        
    def teardown_canvas(self):
        for c in self._constraints:
            self.canvas.solver.remove(c)

    def handles(self):
        return iter(self._handles)

    def pre_update(self, context):
        h = self._handles
        if float(h[NW].x) > float(h[NE].x):
            h[NE].x = h[NW].x
        if float(h[NW].y) > float(h[SW].y):
            h[SW].y = h[NW].y

    def update(self, context):
        pass

    def point(self, context, x, y):
        h = self._handles
        if float(h[NW].x) < x < float(h[SE].x) \
           and float(h[NW].y) < y < float(h[SE].y):
            return 0
        else:
            return 100

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
