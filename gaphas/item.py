"""
Basic items.
"""

__version__ = "$Revision$"
# $HeadURL$

from math import atan2

from matrix import Matrix
from geometry import distance_line_point, distance_rectangle_point
from solver import solvable, WEAK, NORMAL, STRONG
from constraint import EqualsConstraint, LessThanConstraint
from state import observed, reversible_pair, reversible_property, disable_dispatching


class Handle(object):
    """
    Handles are used to support modifications of Items.

    If the handle is connected to an item, the connected_to property should
    refer to the item. A disconnect handler should be provided that handles
    all disconnect behavior (e.g. clean up constraints and connected_to).
    """
    
    _x = solvable()
    _y = solvable()

    def __init__(self, x=0, y=0, strength=NORMAL, connectable=False, movable=True):
        self._x = x
        self._y = y
        self._x.strength = strength
        self._y.strength = strength

        # Flags.. can't have enough of those
        self._connectable = connectable
        self._movable = movable
        self._visible = True
        self._connected_to = None

        # The constraint used to keep the handle visually connected
        self._disconnect = lambda: 0

    @observed
    def _set_x(self, x):
        self._x = x

    x = reversible_property(lambda s: s._x, _set_x, bind={'x': lambda self: float(self.x) })
    disable_dispatching(_set_x)

    @observed
    def _set_y(self, y):
        self._y = y

    y = reversible_property(lambda s: s._y, _set_y, bind={'y': lambda self: float(self.y) })
    disable_dispatching(_set_y)

    @observed
    def _set_connectable(self, connectable):
        self._connectable = connectable

    connectable = reversible_property(lambda s: s._connectable, _set_connectable)

    @observed
    def _set_movable(self, movable):
        self._movable = movable

    movable = reversible_property(lambda s: s._movable, _set_movable)

    @observed
    def _set_visible(self, visible):
        self._visible = visible

    visible = reversible_property(lambda s: s._visible, _set_visible)

    @observed
    def _set_connected_to(self, connected_to):
        self._connected_to = connected_to

    connected_to = reversible_property(lambda s: s._connected_to, _set_connected_to)

    @observed
    def _set_disconnect(self, disconnect):
        self._disconnect = disconnect

    disconnect = reversible_property(lambda s: s._disconnect, _set_disconnect)

    @observed
    def _set_pos(self, pos):
        """
        Set handle position (Item coordinates).
        """
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

    def __str__(self):
        return '<%s object on (%g, %g)>' % (self.__class__.__name__, float(self.x), float(self.y))
    __repr__ = __str__

    def __getitem__(self, index):
        """
        Shorthand for returning the x(0) or y(1) component of the point.

            >>> h = Handle(3, 5)
            >>> h[0]
            Variable(3, 20)
            >>> h[1]
            Variable(5, 20)
        """
        return (self.x, self.y)[index]


class Item(object):
    """
    Base class (or interface) for items on a canvas.Canvas.
    """

    def __init__(self):
        self._canvas = None
        self._matrix = Matrix()

    @observed
    def _set_canvas(self, canvas):
        """
        Set the canvas.
        """
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    def _del_canvas(self):
        """
        Unset the canvas.
        """
        self._set_canvas(None)

    canvas = reversible_property(lambda s: s._canvas, _set_canvas, _del_canvas,
                doc="Set canvas for the item. Application should use " + \
                    "Canvas.add() and Canvas.remove().")

    def setup_canvas(self):
        """
        Called when the canvas is unset for the item.
        This method can be used to create constraints.
        """
        pass

    def teardown_canvas(self):
        """
        Called when the canvas is unset for the item.
        This method can be used to dispose constraints.
        """
        for h in self.handles():
            h.disconnect()

    @observed
    def _set_matrix(self, matrix):
        """
        Set the conversion matrix (parent -> item)
        """
        if not isinstance(matrix, Matrix):
            matrix = Matrix(*matrix)
        self._matrix = matrix

    matrix = reversible_property(lambda s: s._matrix, _set_matrix)

    def request_update(self):
        if self._canvas:
            self._canvas.request_update(self)

    def pre_update(self, context):
        """
        Do small things that have to be done before the "real" update.
        Context has the following attributes:

        - canvas: the owning canvas
        - matrix_i2w: Item to World transformation matrix
        - ... (do I need something for text processing?)
        """
        pass


    def update(self, context):
        """
        Like pre_update(), but this is step 2.
        """
        pass

    def draw(self, context):
        """
        Render the item to a canvas view.
        Context contains the following attributes:

        - matrix_i2w: Item to World transformation matrix (no need to)
        - cairo: the Cairo Context use this one to draw.
        - view: the view that is to be rendered to
        - selected, focused, hovered: view state of items.
        """
        pass

    def handles(self):
        """
        Return a list of handles owned by the item.
        """
        return list()

    def point(self, x, y):
        """
        Get the distance from a point (@x, @y) to the item.
        @x and @y are in item coordinates.
        """
        pass


[ NW,
  NE,
  SE,
  SW ] = xrange(4)

class Element(Item):
    """
    An Element has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Element, self).__init__()
        self._handles = [ h(strength=STRONG) for h in [Handle]*4 ]
        self._constraints = []
        self._min_width = 10
        self._min_height = 10
        self.width = width
        self.height = height

    def _set_width(self, width):
        """
        >>> b=Element()
        >>> b.width = 20
        >>> b.width
        20.0
        >>> b._handles[NW].x
        Variable(0, 30)
        >>> b._handles[SE].x
        Variable(20, 30)
        """
        if width < self.min_width:
            width = self.min_width
        h = self._handles
        h[SE].x = h[NW].x + width

    def _get_width(self):
        """
        Width of the box, calculated as the distance from the left and
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
        >>> b.height = 2
        >>> b.height
        10.0
        >>> b._handles[NW].y
        Variable(0, 30)
        >>> b._handles[SE].y
        Variable(10, 30)
        """
        if height < self.min_height:
            height = self.min_height
        h = self._handles
        h[SE].y = h[NW].y + height

    def _get_height(self):
        """
        Height.
        """
        h = self._handles
        return float(h[SE].y) - float(h[NW].y)

    height = property(_get_height, _set_height)

    @observed
    def _set_min_width(self, min_width):
        """
        """
        self._min_width = max(0, min_width)
        if min_width > self.width:
            self.width = min_width

    min_width = reversible_property(lambda s: s._min_width, _set_min_width)

    @observed
    def _set_min_height(self, min_height):
        """
        """
        self._min_height = max(0, min_height)
        if min_height > self.height:
            self.height = min_height

    min_height = reversible_property(lambda s: s._min_height, _set_min_height)

    def setup_canvas(self):
        """
        >>> from canvas import Canvas
        >>> c=Canvas()
        >>> c.solver._constraints
        set([])
        >>> b = Element()
        >>> c.add(b)
        >>> b.canvas is c
        True
        >>> len(c.solver._constraints)
        8
        >>> len(c.solver._marked_cons)
        0
        >>> c.solver.solve()
        >>> len(c.solver._constraints)
        8
        >>> len(c.solver._marked_cons)
        0
        >>> b._handles[SE].pos = (25,30)
        >>> len(c.solver._marked_cons)
        4
        >>> c.solver.solve()
        >>> float(b._handles[NE].x)
        25.0
        >>> float(b._handles[SW].y)
        30.0
        """
        eq = EqualsConstraint
        lt = LessThanConstraint
        h = self._handles
        add = self.canvas.solver.add_constraint
        self._constraints = [
            add(eq(a=h[NW].y, b=h[NE].y)),
            add(eq(a=h[SW].y, b=h[SE].y)),
            add(eq(a=h[NW].x, b=h[SW].x)),
            add(eq(a=h[NE].x, b=h[SE].x)),
            add(lt(smaller=h[NW].x, bigger=h[NE].x)),
            add(lt(smaller=h[SW].x, bigger=h[SE].x)),
            add(lt(smaller=h[NE].y, bigger=h[SE].y)),
            add(lt(smaller=h[NW].y, bigger=h[SW].y)),
            ]

        # Immediately solve the constraints, ensuring the box is drawn okay
        solve_for = (h[NE].y, h[SW].y, h[SW].x, h[NE].x)
        for c, v in zip(self._constraints, solve_for):
            c.solve_for(v)
        
    def teardown_canvas(self):
        """
        Remove constraints created in setup_canvas().
        >>> from canvas import Canvas
        >>> c=Canvas()
        >>> c.solver._constraints
        set([])
        >>> b = Element()
        >>> c.add(b)
        >>> b.canvas is c
        True
        >>> len(c.solver._constraints)
        8
        >>> b.teardown_canvas()
        >>> len(c.solver._constraints)
        0
        """
        super(Element, self).teardown_canvas()
        for c in self._constraints:
            self.canvas.solver.remove_constraint(c)

    def handles(self):
        """
        The handles.
        """
        return self._handles

    def pre_update(self, context):
        """
        Make sure handles do not overlap during movement.
        Make sure the first handle (normally NW) is located at (0, 0).

        >>> from canvas import Canvas
        >>> c = Canvas()
        >>> e = Element()
        >>> c.add(e)
        >>> e.min_width = e.min_height = 0
        >>> c.update_now()
        >>> e._handles
        [<Handle object on (0, 0)>, <Handle object on (10, 0)>, <Handle object on (10, 10)>, <Handle object on (0, 10)>]
        >>> e._handles[0].x += 1
        >>> map(float, e._handles[0].pos)
        [1.0, 0.0]
        >>> e.pre_update(None)
        >>> e._handles
        [<Handle object on (0, 0)>, <Handle object on (9, 0)>, <Handle object on (9, 10)>, <Handle object on (0, 10)>]
        """
        h_nw = self._handles[0]
        x, y = map(float, h_nw.pos)
        if not x:
            x = float(self._handles[-1].x)
        if x:
            self.matrix.translate(x, 0)
            self._canvas.request_matrix_update(self)
            h_nw.x = 0
            for h in self._handles[1:]:
                h.x -= x
        if not y:
            y = float(self._handles[1].y)
        if y:
            self.matrix.translate(0, y)
            self._canvas.request_matrix_update(self)
            h_nw.y = 0
            for h in self._handles[1:]:
                h.y -= y

        if self.width < self.min_width:
            self.width = self.min_width
        if self.height < self.min_height:
            self.height = self.min_height

    def update(self, context):
        """
        Do nothing during update.
        """
        pass

    def point(self, x, y):
        """
        Distance from the point (x, y) to the item.
        """
        h = self._handles
        hnw, hse = h[NW], h[SE]
        return distance_rectangle_point(map(float, (hnw.x, hnw.y, hse.x, hse.y)), (x, y))


class Line(Item):
    """
    A Line item.

    Properties:
     - fuzziness (0.0..n): an extra margin that should be taken into account
         when calculating the distance from the line (using point()).
     - orthogonal (bool): wherther or not the line should be orthogonal
         (only straight angles)
     - horizontal: first line segment is horizontal
     - line_width: width of the line to be drawn

    This line also supports arrow heads on both the begin and end of the
    line. These are drawn with the methods draw_head(context) and
    draw_tail(context). The coordinate system is altered so the methods do
    not have to know about the angle of the line segment (e.g. drawing a line
    from (10, 10) via (0, 0) to (10, -10) will draw an arrow point).
    """

    def __init__(self):
        super(Line, self).__init__()
        self._handles = [Handle(connectable=True), Handle(10, 10, connectable=True)]

        self._line_width = 2
        self._fuzziness = 0
        self._orthogonal = []
        self._horizontal = False
        self._head_angle = self._tail_angle = 0

    @observed
    def _set_line_width(self, line_width):
        self._line_width = line_width

    line_width = reversible_property(lambda s: s._line_width, _set_line_width)

    @observed
    def _set_fuzziness(self, fuzziness):
        self._fuzziness = fuzziness

    fuzziness = reversible_property(lambda s: s._fuzziness, _set_fuzziness)

    @observed
    def _set_orthogonal(self, orthogonal):
        """
        >>> a = Line()
        >>> a.orthogonal
        False
        """
        if not self.canvas:
            self._orthogonal = orthogonal and [ None ] or []
            return

        for c in self._orthogonal:
            self.canvas.solver.remove_constraint(c)
            self._orthogonal = []

        if not orthogonal:
            return

        h = self._handles
        if len(h) < 3:
            self.split_segment(0)
        eq = EqualsConstraint #lambda a, b: a - b
        add = self.canvas.solver.add_constraint
        cons = self._orthogonal
        rest = self._horizontal and 1 or 0
        for pos, (h0, h1) in enumerate(zip(h, h[1:])):
            if pos % 2 == rest: # odd
                cons.append(add(eq(a=h0.x, b=h1.x)))
            else:
                cons.append(add(eq(a=h0.y, b=h1.y)))
            self.canvas.solver.mark_dirty(h1.x, h1.y)
        self.request_update()

    orthogonal = reversible_property(lambda s: bool(s._orthogonal), _set_orthogonal)

    @observed
    def _set_horizontal(self, horizontal):
        """
        >>> line = Line()
        >>> line.horizontal
        False
        >>> line.horizontal = False
        >>> line.horizontal
        False
        """
        self._horizontal = horizontal
        self._set_orthogonal(self._orthogonal)

    horizontal = reversible_property(lambda s: s._horizontal, _set_horizontal)

    def setup_canvas(self):
        """
        Setup constraints. In this case orthogonal.
        """
        self.orthogonal = self.orthogonal

    def teardown_canvas(self):
        """
        Remove constraints created in setup_canvas().
        """
        super(Line, self).teardown_canvas()
        for c in self._orthogonal:
            self.canvas.solver.remove_constraint(c)

    @observed
    def split_segment(self, segment, parts=2):
        """
        Split one segment in the Line in @parts equal pieces.
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
        def do_split(segment, parts):
            h0 = self._handles[segment]
            h1 = self._handles[segment + 1]
            dx, dy = h1.x - h0.x, h1.y - h0.y
            new_h = Handle(h0.x + dx / parts, h0.y + dy / parts, strength=WEAK)
            self._handles.insert(segment + 1, new_h)
            # TODO: reconnect connected handles.
            if parts > 2:
                do_split(segment + 1, parts - 1)
        do_split(segment, parts)
        self.orthogonal = self.orthogonal

    @observed
    def merge_segment(self, segment, parts=2):
        """
        Merge the @segment and the next.
        The parts parameter indicates how many segments should be merged

        >>> a = Line()
        >>> a.handles()[1].pos = (20, 0)
        >>> a.split_segment(0)
        >>> a.handles()
        [<Handle object on (0, 0)>, <Handle object on (10, 0)>, <Handle object on (20, 0)>]
        >>> a.merge_segment(0)
        >>> len(a.handles())
        2
        >>> try: a.merge_segment(0)
        ... except AssertionError: print 'okay'
        okay
        """
        assert len(self._handles) > 2, 'Not enough segments'
        if 0 >= segment > len(self._handles) - 1:
            raise IndexError("index out of range (0 > %d > %d)" % (segment, len(self._handles) - 1))
        if segment == 0: segment = 1
        del self._handles[segment]
        if parts > 2:
            merge_segment(segment, parts - 1)
        else:
            # Force orthogonal constraints to be recreated
            self.orthogonal = self.orthogonal

    reversible_pair(split_segment, merge_segment)

    def handles(self):
        return self._handles
    
    def opposite(self, handle):
        """
        Given the handle of one end of the line, return the other end.
        """
        handles = self._handles
        if handle is handles[0]:
            return handles[-1]
        elif handle is handles[-1]:
            return handles[0]
        else:
            raise KeyError('Handle is not an end handle')

    def update(self, context):
        """
        """
        super(Line, self).update(context)
        h0, h1 = self._handles[:2]
        self._head_angle = atan2(h1.y - h0.y, h1.x - h0.x)
        h1, h0 = self._handles[-2:]
        self._tail_angle = atan2(h1.y - h0.y, h1.x - h0.x)

    def closest_segment(self, x, y):
        """
        Obtain a tuple (distance, point_on_line, segment).
        Distance is the distance from point to the closest line segment 
        Point_on_line is the reflection of the point on the line.
        Segment is the line segment closest to (x, y)

        >>> a = Line()
        >>> a.closest_segment(4, 5)
        (0.70710678118654757, (4.5, 4.5), 0)
        """
        h = self._handles

        # create a list of (distance, point_on_line) tuples:
        distances = map(distance_line_point, h[:-1], h[1:], [(x, y)] * (len(h) - 1))
        distances, pols = zip(*distances)
        return reduce(min, zip(distances, pols, range(len(distances))))

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
        distance, point, segment = self.closest_segment(x, y)
        return max(0, distance - self.fuzziness)

    def draw_head(self, context):
        """
        Default head drawer: move cursor to the first handle.
        """
        context.cairo.move_to(0, 0)

    def draw_tail(self, context):
        """
        Default tail drawer: draw line to the last handle.
        """
        context.cairo.line_to(0, 0)


    def draw(self, context):
        """
        Draw the line itself.
        See Item.draw(context).
        """
        def draw_line_end(handle, angle, draw):
            cr = context.cairo
            cr.save()
            try:
                cr.translate(handle.x, handle.y)
                cr.rotate(angle)
                draw(context)
            finally:
                cr.restore()
        cr = context.cairo
        cr.set_line_width(self.line_width)
        draw_line_end(self._handles[0], self._head_angle, self.draw_head)
        for h in self._handles[1:-1]:
            cr.line_to(float(h.x), float(h.y))
        h0, h1 = self._handles[-2:]
        draw_line_end(self._handles[-1], self._tail_angle, self.draw_tail)
        cr.stroke()


__test__ = {
    'Line._set_orthogonal': Line._set_orthogonal,
    'Line._set_horizontal': Line._set_horizontal,
    'Line.split_segment': Line.split_segment,
    'Line.merge_segment': Line.merge_segment,
    }


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
