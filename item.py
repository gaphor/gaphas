
from geometry import Matrix, distance_line_point
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
        """Set handle position (Item coordinates).
        """
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

    def __str__(self):
        return '<%s object on (%g, %g)>' % (self.__class__.__name__, float(self.x), float(self.y))
    __repr__ = __str__

    def __getitem__(self, index):
        """
        >>> h = Handle(3, 5)
        >>> h[0]
        Variable(3, 20)
        >>> h[1]
        Variable(5, 20)
        """
        return (self.x, self.y)[index]

#    def update(self, context):
#        """Update the handle. @context has the following attributes:
#         - item: the owning item
#         - matrix_i2w: Item to World transformation matrix
#        """
#        pass


class Item(object):
    """Base class (or interface) for items on a canvas.Canvas.
    """

    def __init__(self):
        self._canvas = None
        self._matrix = Matrix()

    def _set_canvas(self, canvas):
        """Set the canvas.
        """
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    def _del_canvas(self):
        """Unset the canvas.
        """
        self.teardown_canvas()
        self._canvas = None

    canvas = property(lambda s: s._canvas, _set_canvas, _del_canvas)

    def setup_canvas(self):
        """Called when the canvas is unset for the item.
        This method can be used to create constraints.
        """
        pass

    def teardown_canvas(self):
        """Called when the canvas is unset for the item.
        This method can be used to dispose constraints.
        """
        pass

    def _set_matrix(self, matrix):
        """Set the conversion matrix (parent -> item)
        """
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

    def point(self, x, y):
        """Get the distance from a point (@x, @y) to the item.
        @x and @y are in item coordinates.
        """
        pass


[ NW,
  NE,
  SW,
  SE ] = xrange(4)

class Element(Item):
    """ An Element has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """
    min_width = solvable(strength=100)
    min_height = solvable(strength=100)

    def __init__(self, width=10, height=10):
        super(Element, self).__init__()
        #self._handles = [Handle(0, 0), Handle(width, 0),
        #                 Handle(0, height), Handle(width, height)]
        self._handles = [ h() for h in [Handle]*4 ]
        self._constraints = []
        self.width = width
        self.height = height
        self.min_width = 10
        self.min_height = 10
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
        """Width of the box, calculated as the distance from the left and
        right handle.
        """
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
        """Height.
        """
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
        eq = lambda a, b: a - b
        h = self._handles
        self._constraints = [
            self.canvas.solver.add_constraint(eq, a=h[NW].y, b=h[NE].y),
            self.canvas.solver.add_constraint(eq, a=h[SW].y, b=h[SE].y),
            self.canvas.solver.add_constraint(eq, a=h[NW].x, b=h[SW].x),
            self.canvas.solver.add_constraint(eq, a=h[NE].x, b=h[SE].x)
            ]
        self.canvas.solver.mark_dirty(h[NW].x)
        self.canvas.solver.mark_dirty(h[NW].y)
        self.canvas.solver.mark_dirty(h[SE].x)
        self.canvas.solver.mark_dirty(h[SE].y)
        
    def teardown_canvas(self):
        """Remove constraints created in setup_canvas().
        """
        for c in self._constraints:
            self.canvas.solver.remove(c)

    def handles(self):
        """The handles.
        """
        return iter(self._handles)

    def pre_update(self, context):
        """Make sure handles do not overlap during movement.
        """
        h = self._handles
        if float(h[NW].x) > float(h[NE].x):
            h[NE].x = h[NW].x
        if float(h[NW].y) > float(h[SW].y):
            h[SW].y = h[NW].y

    def update(self, context):
        """Do nothing dureing update.
        """
        pass

    def point(self, x, y):
        """Distance from the point (x, y) to the item.
        """
        h = self._handles
        if float(h[NW].x) < x < float(h[SE].x) \
           and float(h[NW].y) < y < float(h[SE].y):
            return 0
        else:
            return 100


class Line(Item):
    """A Line item.
    """

    def __init__(self):
        super(Line, self).__init__()
        self._handles = [Handle(), Handle(10, 10)]

    def split_segment(self, segment, parts=2):
        """Split one segment in the Line in @parts pieces.
        @segment 0 is the first segment (between handles 0 and 1).
        The min number of parts is 2.

        >>> a = Line()
        >>> a.handles()[1].pos = (20, 0)
        >>> len(a.handles())
        2
        >>> a.split_segment(0)
        >>> len(a.handles())
        3
        >>> a.handles()[1]
        <Handle object on (10, 0)>
        >>> b = Line()
        >>> b.handles()[1].pos = (20, 16)
        >>> b.handles()
        [<Handle object on (0, 0)>, <Handle object on (20, 16)>]
        >>> b.split_segment(0, parts=4)
        >>> len(b.handles())
        5
        >>> b.handles()
        [<Handle object on (0, 0)>, <Handle object on (5, 4)>, <Handle object on (10, 8)>, <Handle object on (15, 12)>, <Handle object on (20, 16)>]
        """
        assert parts >= 2
        assert segment >= 0
        h0 = self._handles[segment]
        h1 = self._handles[segment + 1]
        dx, dy = h1.x - h0.x, h1.y - h0.y
        new_h = Handle(h0.x + dx / parts, h0.y + dy / parts)
        self._handles.insert(segment + 1, new_h)
        # TODO: reconnect connected handles.
        if parts > 2:
            self.split_segment(segment + 1, parts - 1)

    def merge_segment(self, segment):
        """Merge the @segment and the next.

        >>> a = Line()
        >>> a.handles()[1].pos = (20, 0)
        >>> a.split_segment(0)
        >>> len(a.handles())
        3
        >>> a.merge_segment(0)
        >>> len(a.handles())
        2
        >>> try: a.merge_segment(0)
        ... except AssertionError: print 'okay'
        okay
        """
        assert len(self._handles) > 2, 'Not enough segments'
        # TODO: recreate constraints that use self._handles[segment + 1]
        del self._handles[segment + 1]

    def handles(self):
        return self._handles

    def _closest_segment(self, x, y):
        """Obtain a tuple (distance, point_on_line, segment).
        Distance is the distance from point to the closest line segment 
        Point_on_line is the reflection of the point on the line.
        TODO: Segment is the line segment closest to (x, y)
        """
        h = self._handles
        distances = map(distance_line_point, h[:-1], h[1:], [(x, y)] * (len(h) - 1))
        #print zip(distances, range(len(distances)))
        return reduce(min, distances)

    def point(self, x, y):
        """
        >>> a = Line()
        >>> a.handles()[1].pos = 30, 30
        >>> a.split_segment(0)
        >>> a.handles()[1].pos = 25, 5
        >>> a.point(-1, 0)
        1.0
        >>> '%.3f' % a.point(5, 4)
        '2.942'
        >>> '%.3f' % a.point(29, 29)
        '0.784'
        """
        h = self._handles
        fuzzyness = 1
        distance, point = self._closest_segment(x, y)
        return max(0, distance - fuzzyness)

    def _draw_line(self, context):
        """Draw the line itself.
        """
        c = context.cairo
        h = self._handles[0]
        c.move_to(float(h.x), float(h.y))
        for h in self._handles[1:]:
            c.line_to(float(h.x), float(h.y))
        c.stroke()

    def draw(self, context):
        """See Item.draw(context).
        """
        self._draw_line(context)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
