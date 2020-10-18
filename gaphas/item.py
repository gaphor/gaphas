"""Basic items."""
from math import atan2
from typing import Optional

from gaphas.connector import Handle, LinePort
from gaphas.constraint import (
    Constraint,
    EqualsConstraint,
    LessThanConstraint,
    LineAlignConstraint,
    LineConstraint,
)
from gaphas.geometry import distance_line_point, distance_rectangle_point
from gaphas.matrix import Matrix
from gaphas.solver import REQUIRED, VERY_STRONG, WEAK, solvable
from gaphas.state import (
    observed,
    reversible_method,
    reversible_pair,
    reversible_property,
)


class Item:
    """Base class (or interface) for items on a canvas.Canvas.

    Attributes:

    - matrix: item's transformation matrix
    - canvas: canvas, which owns an item
    - constraints: list of item constraints, automatically registered
      when the item is added to a canvas; may be extended in subclasses

    Private:

    - _canvas:      canvas, which owns an item
    - _handles:     list of handles owned by an item
    - _ports:       list of ports, connectable areas of an item
    - _constraints: list of constraints that belong to the lifecycle of this item
    """

    def __init__(self):
        self._canvas = None
        self._matrix = Matrix()
        self._handles = []
        self._constraints = []
        self._ports = []

    @observed
    def _set_canvas(self, canvas):
        """Set the canvas.

        Should only be called from Canvas.add and Canvas.remove().
        """
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    canvas = reversible_property(
        lambda s: s._canvas, _set_canvas, doc="Canvas owning this item"
    )

    constraints = property(lambda s: s._constraints, doc="Item constraints")

    def setup_canvas(self):
        """Called when the canvas is set for the item.

        This method can be used to create constraints.
        """
        add = self.canvas.solver.add_constraint
        for c in self._constraints:
            add(c)

    def teardown_canvas(self):
        """Called when the canvas is unset for the item.

        This method can be used to dispose constraints.
        """
        self.canvas.disconnect_item(self)

        remove = self.canvas.solver.remove_constraint
        for c in self._constraints:
            remove(c)

    @observed
    def _set_matrix(self, matrix):
        """Set the conversion matrix (parent -> item)"""
        if not isinstance(matrix, Matrix):
            matrix = Matrix(*matrix)
        self._matrix = matrix

    matrix = reversible_property(lambda s: s._matrix, _set_matrix)

    def request_update(self, update=True, matrix=True):
        if self._canvas:
            self._canvas.request_update(self, update=update, matrix=matrix)

    def pre_update(self, context):
        """Perform any changes before item update here, for example:

        - change matrix
        - move handles

        Gaphas does not guarantee that any canvas invariant is valid
        at this point (i.e. constraints are not solved, first handle
        is not in position (0, 0), etc).
        """
        pass

    def post_update(self, context):
        """Method called after item update.

        If some variables should be used during drawing or in another
        update, then they should be calculated in post method.

        Changing matrix or moving handles programmatically is really
        not advised to be performed here.

        All canvas invariants are true.
        """
        pass

    def normalize(self):
        """Update handle positions of the item, so the first handle is always
        located at (0, 0).

        Note that, since this method basically does some housekeeping
        during the update phase, there's no need to keep track of the
        changes.

        Alternative implementation can also be created, e.g. set (0,
        0) in the center of a circle or change it depending on the
        location of a rotation point.

        Returns ``True`` if some updates have been done, ``False``
        otherwise.

        See ``canvas._normalize()`` for tests.
        """
        updated = False
        handles = self._handles
        if handles:
            x, y = list(map(float, handles[0].pos))
            if x:
                self.matrix.translate(x, 0)
                updated = True
                for h in handles:
                    h.pos.x -= x
            if y:
                self.matrix.translate(0, y)
                updated = True
                for h in handles:
                    h.pos.y -= y
        return updated

    def draw(self, context):
        """Render the item to a canvas view. Context contains the following
        attributes:

        - cairo: the Cairo Context use this one to draw
        - view: the view that is to be rendered to
        - selected, focused, hovered, dropzone: view state of items
          (True/False)
        - draw_all: a request to draw everything, for bounding box
          calculations
        """
        pass

    def handles(self):
        """Return a list of handles owned by the item."""
        return self._handles

    def ports(self):
        """Return list of ports."""
        return self._ports

    def point(self, pos):
        """Get the distance from a point (``x``, ``y``) to the item.

        ``x`` and ``y`` are in item coordinates.
        """
        pass

    def constraint(
        self,
        horizontal=None,
        vertical=None,
        left_of=None,
        above=None,
        line=None,
        delta=0.0,
        align=None,
    ):
        """Utility (factory) method to create item's internal constraint
        between two positions or between a position and a line.

        Position is a tuple of coordinates, i.e. ``(2, 4)``.

        Line is a tuple of positions, i.e. ``((2, 3), (4, 2))``.

        This method shall not be used to create constraints between
        two different items.

        Created constraint is returned.

        :Parameters:
         horizontal=(p1, p2)
            Keep positions ``p1`` and ``p2`` aligned horizontally.
         vertical=(p1, p2)
            Keep positions ``p1`` and ``p2`` aligned vertically.
         left_of=(p1, p2)
            Keep position ``p1`` on the left side of position ``p2``.
         above=(p1, p2)
            Keep position ``p1`` above position ``p2``.
         line=(p, l)
            Keep position ``p`` on line ``l``.
        """
        cc: Optional[Constraint] = None  # created constraint
        if horizontal:
            p1, p2 = horizontal
            cc = EqualsConstraint(p1[1], p2[1], delta)
        elif vertical:
            p1, p2 = vertical
            cc = EqualsConstraint(p1[0], p2[0], delta)
        elif left_of:
            p1, p2 = left_of
            cc = LessThanConstraint(p1[0], p2[0], delta)
        elif above:
            p1, p2 = above
            cc = LessThanConstraint(p1[1], p2[1], delta)
        elif line:
            pos, line_l = line
            if align is None:
                cc = LineConstraint(line=line_l, point=pos)
            else:
                cc = LineAlignConstraint(
                    line=line_l, point=pos, align=align, delta=delta
                )
        else:
            raise ValueError("Constraint incorrectly specified")
        assert cc is not None
        self._constraints.append(cc)
        return cc


[NW, NE, SE, SW] = list(range(4))


class Element(Item):
    """An Element has 4 handles (for a start)::

    NW +---+ NE    |   | SW +---+ SE
    """

    min_width = solvable(strength=REQUIRED, varname="_min_width")
    min_height = solvable(strength=REQUIRED, varname="_min_height")

    def __init__(self, width=10, height=10):
        super().__init__()
        self._handles = [h(strength=VERY_STRONG) for h in [Handle] * 4]

        handles = self._handles
        h_nw = handles[NW]
        h_ne = handles[NE]
        h_sw = handles[SW]
        h_se = handles[SE]

        # edge of element define default element ports
        self._ports = [
            LinePort(h_nw.pos, h_ne.pos),
            LinePort(h_ne.pos, h_se.pos),
            LinePort(h_se.pos, h_sw.pos),
            LinePort(h_sw.pos, h_nw.pos),
        ]

        # initialize min_x variables
        self.min_width, self.min_height = 10, 10

        self.constraint(horizontal=(h_nw.pos, h_ne.pos))
        self.constraint(horizontal=(h_sw.pos, h_se.pos))
        self.constraint(vertical=(h_nw.pos, h_sw.pos))
        self.constraint(vertical=(h_ne.pos, h_se.pos))

        # create minimal size constraints
        self.constraint(left_of=(h_nw.pos, h_se.pos), delta=self.min_width)
        self.constraint(above=(h_nw.pos, h_se.pos), delta=self.min_height)

        self.width = width
        self.height = height

        # TODO: constraints that calculate width and height based on handle pos
        # self.constraints.append(EqualsConstraint(p1[1], p2[1], delta))

    def setup_canvas(self):
        super().setup_canvas()

        # Trigger solver to honour width/height by SE handle pos
        self._handles[SE].pos.x.dirty()
        self._handles[SE].pos.y.dirty()

    def _set_width(self, width):
        """
        >>> b=Element()
        >>> b.width = 20
        >>> b.width
        20.0
        >>> b._handles[NW].pos.x
        Variable(0, 40)
        >>> b._handles[SE].pos.x
        Variable(20, 40)
        """
        h = self._handles
        h[SE].pos.x = h[NW].pos.x + width

    def _get_width(self):
        """Width of the box, calculated as the distance from the left and right
        handle."""
        h = self._handles
        return float(h[SE].pos.x) - float(h[NW].pos.x)

    width = property(_get_width, _set_width)

    def _set_height(self, height):
        """
        >>> b=Element()
        >>> b.height = 20
        >>> b.height
        20.0
        >>> b.height = 2
        >>> b.height
        2.0
        >>> b._handles[NW].pos.y
        Variable(0, 40)
        >>> b._handles[SE].pos.y
        Variable(2, 40)
        """
        h = self._handles
        h[SE].pos.y = h[NW].pos.y + height

    def _get_height(self):
        """Height."""
        h = self._handles
        return float(h[SE].pos.y) - float(h[NW].pos.y)

    height = property(_get_height, _set_height)

    def normalize(self):
        """Normalize only NW and SE handles."""
        updated = False
        handles = (self._handles[NW], self._handles[SE])
        x, y = list(map(float, handles[0].pos))
        if x:
            self.matrix.translate(x, 0)
            updated = True
            for h in handles:
                h.pos.x -= x
        if y:
            self.matrix.translate(0, y)
            updated = True
            for h in handles:
                h.pos.y -= y
        return updated

    def point(self, pos):
        """Distance from the point (x, y) to the item.

        >>> e = Element()
        >>> e.point((20, 10))
        10.0
        """
        h = self._handles
        pnw, pse = h[NW].pos, h[SE].pos
        return distance_rectangle_point(
            list(map(float, (pnw.x, pnw.y, pse.x, pse.y))), pos
        )


class Line(Item):
    """A Line item.

    Properties:
     - fuzziness (0.0..n): an extra margin that should be taken into
         account when calculating the distance from the line (using
         point()).
     - orthogonal (bool): whether or not the line should be
         orthogonal (only straight angles)
     - horizontal: first line segment is horizontal
     - line_width: width of the line to be drawn

    This line also supports arrow heads on both the begin and end of
    the line. These are drawn with the methods draw_head(context) and
    draw_tail(context). The coordinate system is altered so the
    methods do not have to know about the angle of the line segment
    (e.g. drawing a line from (10, 10) via (0, 0) to (10, -10) will
    draw an arrow point).
    """

    def __init__(self):
        super().__init__()
        self._handles = [Handle(connectable=True), Handle((10, 10), connectable=True)]
        self._ports = []
        self._update_ports()

        self._line_width = 2
        self._fuzziness = 0
        self._orthogonal_constraints = []
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

    def _update_orthogonal_constraints(self, orthogonal):
        """Update the constraints required to maintain the orthogonal line.

        The actual constraints attribute (``_orthogonal_constraints``)
        is observed, so the undo system will update the contents
        properly
        """
        if not self.canvas:
            self._orthogonal_constraints = orthogonal and [None] or []
            return

        for c in self._orthogonal_constraints:
            self.canvas.solver.remove_constraint(c)
        del self._orthogonal_constraints[:]

        if not orthogonal:
            return

        h = self._handles
        # if len(h) < 3:
        #    self.split_segment(0)
        eq = EqualsConstraint  # lambda a, b: a - b
        add = self.canvas.solver.add_constraint
        cons = []
        rest = self._horizontal and 1 or 0
        for pos, (h0, h1) in enumerate(zip(h, h[1:])):
            p0 = h0.pos
            p1 = h1.pos
            if pos % 2 == rest:  # odd
                cons.append(add(eq(a=p0.x, b=p1.x)))
            else:
                cons.append(add(eq(a=p0.y, b=p1.y)))
            p1.x.notify()
            p1.y.notify()
        self._set_orthogonal_constraints(cons)
        self.request_update()

    @observed
    def _set_orthogonal_constraints(self, orthogonal_constraints):
        """Setter for the constraints maintained.

        Required for the undo system.
        """
        self._orthogonal_constraints = orthogonal_constraints

    reversible_property(
        lambda s: s._orthogonal_constraints, _set_orthogonal_constraints
    )

    @observed
    def _set_orthogonal(self, orthogonal):
        """
        >>> a = Line()
        >>> a.orthogonal
        False
        """
        if orthogonal and len(self.handles()) < 3:
            raise ValueError("Can't set orthogonal line with less than 3 handles")
        self._update_orthogonal_constraints(orthogonal)

    orthogonal = reversible_property(
        lambda s: bool(s._orthogonal_constraints), _set_orthogonal
    )

    @observed
    def _inner_set_horizontal(self, horizontal):
        self._horizontal = horizontal

    reversible_method(
        _inner_set_horizontal,
        _inner_set_horizontal,
        {"horizontal": lambda horizontal: not horizontal},
    )

    def _set_horizontal(self, horizontal):
        """
        >>> line = Line()
        >>> line.horizontal
        False
        >>> line.horizontal = False
        >>> line.horizontal
        False
        """
        self._inner_set_horizontal(horizontal)
        self._update_orthogonal_constraints(self.orthogonal)

    horizontal = reversible_property(lambda s: s._horizontal, _set_horizontal)

    def setup_canvas(self):
        """Setup constraints.

        In this case orthogonal.
        """
        super().setup_canvas()
        self._update_orthogonal_constraints(self.orthogonal)

    def teardown_canvas(self):
        """Remove constraints created in setup_canvas()."""
        super().teardown_canvas()
        for c in self._orthogonal_constraints:
            self.canvas.solver.remove_constraint(c)

    @observed
    def _reversible_insert_handle(self, index, handle):
        self._handles.insert(index, handle)

    @observed
    def _reversible_remove_handle(self, handle):
        self._handles.remove(handle)

    reversible_pair(
        _reversible_insert_handle,
        _reversible_remove_handle,
        bind1={"index": lambda self, handle: self._handles.index(handle)},
    )

    @observed
    def _reversible_insert_port(self, index, port):
        self._ports.insert(index, port)

    @observed
    def _reversible_remove_port(self, port):
        self._ports.remove(port)

    reversible_pair(
        _reversible_insert_port,
        _reversible_remove_port,
        bind1={"index": lambda self, port: self._ports.index(port)},
    )

    def _create_handle(self, pos, strength=WEAK):
        return Handle(pos, strength=strength)

    def _create_port(self, p1, p2):
        return LinePort(p1, p2)

    def _update_ports(self):
        """Update line ports.

        This destroys all previously created ports and should only be
        used when initializing the line.
        """
        assert len(self._handles) >= 2, "Not enough segments"
        self._ports = []
        handles = self._handles
        for h1, h2 in zip(handles[:-1], handles[1:]):
            self._ports.append(self._create_port(h1.pos, h2.pos))

    def opposite(self, handle):
        """Given the handle of one end of the line, return the other end."""
        handles = self._handles
        if handle is handles[0]:
            return handles[-1]
        elif handle is handles[-1]:
            return handles[0]
        else:
            raise KeyError("Handle is not an end handle")

    def post_update(self, context):
        """"""
        super().post_update(context)
        h0, h1 = self._handles[:2]
        p0, p1 = h0.pos, h1.pos
        self._head_angle = atan2(p1.y - p0.y, p1.x - p0.x)  # type: ignore[assignment]
        h1, h0 = self._handles[-2:]
        p1, p0 = h1.pos, h0.pos
        self._tail_angle = atan2(p1.y - p0.y, p1.x - p0.x)  # type: ignore[assignment]

    def point(self, pos):
        """
        >>> a = Line()
        >>> a.handles()[1].pos = 25, 5
        >>> a._handles.append(a._create_handle((30, 30)))
        >>> a.point((-1, 0))
        1.0
        >>> f"{a.point((5, 4)):.3f}
        '2.942'
        >>> f"{a.point((29, 29)):.3f}
        '0.784'
        """
        hpos = [h.pos for h in self._handles]

        distance, _point = min(
            map(distance_line_point, hpos[:-1], hpos[1:], [pos] * (len(hpos) - 1))
        )
        return max(0, distance - self.fuzziness)

    def draw_head(self, context):
        """Default head drawer: move cursor to the first handle."""
        context.cairo.move_to(0, 0)

    def draw_tail(self, context):
        """Default tail drawer: draw line to the last handle."""
        context.cairo.line_to(0, 0)

    def draw(self, context):
        """Draw the line itself.

        See Item.draw(context).
        """

        def draw_line_end(pos, angle, draw):
            cr = context.cairo
            cr.save()
            try:
                cr.translate(*pos)
                cr.rotate(angle)
                draw(context)
            finally:
                cr.restore()

        cr = context.cairo
        cr.set_line_width(self.line_width)
        draw_line_end(self._handles[0].pos, self._head_angle, self.draw_head)
        for h in self._handles[1:-1]:
            cr.line_to(*h.pos)
        draw_line_end(self._handles[-1].pos, self._tail_angle, self.draw_tail)
        cr.stroke()


__test__ = {"Line._set_orthogonal": Line._set_orthogonal}
