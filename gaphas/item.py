"""Basic items."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2
from typing import TYPE_CHECKING, Iterable, Protocol, Sequence, runtime_checkable

from cairo import Context as CairoContext

from gaphas.constraint import Constraint, EqualsConstraint, constraint
from gaphas.geometry import distance_line_point, distance_rectangle_border_point
from gaphas.handle import Handle
from gaphas.matrix import Matrix
from gaphas.port import LinePort, Port
from gaphas.solver import REQUIRED, VERY_STRONG, variable

if TYPE_CHECKING:
    from gaphas.connections import Connections


@dataclass(frozen=True)
class DrawContext:
    cairo: CairoContext
    selected: bool
    focused: bool
    hovered: bool


@runtime_checkable
class Item(Protocol):
    """This protocol should be implemented by model items.

    All items that are rendered on a view.
    """

    @property
    def matrix(self) -> Matrix:
        """The "local", item-to-parent matrix."""

    @property
    def matrix_i2c(self) -> Matrix:
        """Matrix from item to toplevel."""

    def handles(self) -> Sequence[Handle]:
        """Return a list of handles owned by the item."""

    def ports(self) -> Sequence[Port]:
        """Return list of ports owned by the item."""

    def point(self, x: float, y: float) -> float:
        """Get the distance from a point (``x``, ``y``) to the item.

        ``x`` and ``y`` are in item coordinates.

        A distance of 0 means the point is on the item.
        """

    def draw(self, context: DrawContext) -> None:
        """Render the item to a canvas view. Context contains the following
        attributes:

        * `cairo`: the CairoContext use this one to draw
        * `selected`, `focused`, `hovered`: view state of items
          (True/False)
        """


def matrix_i2i(from_item: Item, to_item: Item) -> Matrix:
    i2c = from_item.matrix_i2c
    c2i = to_item.matrix_i2c.inverse()
    return i2c.multiply(c2i)


class Matrices:
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._matrix = Matrix()
        self._matrix_i2c = Matrix()

    @property
    def matrix(self) -> Matrix:
        return self._matrix

    @property
    def matrix_i2c(self) -> Matrix:
        return self._matrix_i2c


[NW, NE, SE, SW] = list(range(4))


class Element(Matrices):
    """An Element has 4 handles (for a start):

    .. code-block:: text

       NW +---+ NE
          |   |
       SW +---+ SE
    """

    min_width = variable(strength=REQUIRED, varname="_min_width")
    min_height = variable(strength=REQUIRED, varname="_min_height")

    def __init__(
        self,
        connections: Connections,
        width: float = 10,
        height: float = 10,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
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

        add = connections.add_constraint
        add(self, constraint(horizontal=(h_nw.pos, h_ne.pos)))
        add(self, constraint(horizontal=(h_sw.pos, h_se.pos)))
        add(self, constraint(vertical=(h_nw.pos, h_sw.pos)))
        add(self, constraint(vertical=(h_ne.pos, h_se.pos)))

        # create minimal size constraints
        add(self, constraint(left_of=(h_nw.pos, h_se.pos), delta=self.min_width))
        add(self, constraint(above=(h_nw.pos, h_se.pos), delta=self.min_height))

        self.width = width
        self.height = height

        # Trigger solver to honour width/height by SE handle pos
        self._handles[SE].pos.x.dirty()
        self._handles[SE].pos.y.dirty()

    @property
    def width(self) -> float:
        """Width of the box, calculated as the distance from the left and right
        handle."""
        h = self._handles
        return float(h[SE].pos.x) - float(h[NW].pos.x)

    @width.setter
    def width(self, width: float) -> None:
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
        h[SE].pos.x = h[NE].pos.x = h[NW].pos.x + width

    @property
    def height(self) -> float:
        """Height."""
        h = self._handles
        return float(h[SE].pos.y) - float(h[NW].pos.y)

    @height.setter
    def height(self, height: float) -> None:
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
        h[SE].pos.y = h[SW].pos.y = h[NW].pos.y + height

    def handles(self) -> Sequence[Handle]:
        """Return a list of handles owned by the item."""
        return self._handles

    def ports(self) -> Sequence[Port]:
        """Return list of ports."""
        return self._ports

    def point(self, x: float, y: float) -> float:
        """Distance from the point (x, y) to the item.

        >>> e = Element()
        >>> e.point(20, 10)
        10.0
        """
        h = self._handles
        x0, y0 = h[NW].pos
        x1, y1 = h[SE].pos
        return distance_rectangle_border_point((x0, y0, x1 - x0, y1 - y0), (x, y))

    def draw(self, context: DrawContext) -> None:
        pass


def create_orthogonal_constraints(
    handles: Sequence[Handle], horizontal: bool
) -> Iterable[Constraint]:
    rest = 1 if horizontal else 0
    for pos, (h0, h1) in enumerate(zip(handles, handles[1:])):
        p0 = h0.pos
        p1 = h1.pos
        if pos % 2 == rest:
            yield EqualsConstraint(a=p0.x, b=p1.x)
        else:
            yield EqualsConstraint(a=p0.y, b=p1.y)


class Line(Matrices):
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

    def __init__(self, connections: Connections, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._connections = connections
        self._handles = [Handle(connectable=True), Handle((10, 10), connectable=True)]
        self._ports: list[Port] = []
        self._update_ports()

        self._line_width = 2.0
        self._fuzziness = 0.0
        self._horizontal = False
        self._orthogonal = False
        self._orthogonal_constraints: list[Constraint] = []

    @property
    def head(self) -> Handle:
        return self._handles[0]

    @property
    def tail(self) -> Handle:
        return self._handles[-1]

    @property
    def line_width(self) -> float:
        return self._line_width

    @line_width.setter
    def line_width(self, line_width: float) -> None:
        self._line_width = line_width

    @property
    def fuzziness(self) -> float:
        return self._fuzziness

    @fuzziness.setter
    def fuzziness(self, fuzziness: float) -> None:
        self._fuzziness = fuzziness

    def update_orthogonal_constraints(self) -> None:
        """Update the constraints required to maintain the orthogonal line."""
        # Use public `horizontal` and `orthogonal` field, so properties can be overwritten
        for c in self._orthogonal_constraints:
            self._connections.remove_constraint(self, c)
        del self._orthogonal_constraints[:]

        if not self.orthogonal or len(self._handles) < 3:
            return

        add = self._connections.add_constraint
        cons = [
            add(self, c)
            for c in create_orthogonal_constraints(self._handles, self.horizontal)
        ]
        self._set_orthogonal_constraints(cons)

    def _set_orthogonal_constraints(
        self, orthogonal_constraints: list[Constraint]
    ) -> None:
        """Setter for the constraints maintained.

        Required for the undo system.
        """
        self._orthogonal_constraints = orthogonal_constraints

    @property
    def orthogonal(self) -> bool:
        return self._orthogonal

    @orthogonal.setter
    def orthogonal(self, orthogonal: bool) -> None:
        """
        >>> a = Line()
        >>> a.orthogonal
        False
        """
        self._orthogonal = True
        self.update_orthogonal_constraints()

    @property
    def horizontal(self) -> bool:
        return self._horizontal

    @horizontal.setter
    def horizontal(self, horizontal: bool) -> None:
        """
        >>> line = Line()
        >>> line.horizontal
        False
        >>> line.horizontal = False
        >>> line.horizontal
        False
        """
        self._horizontal = horizontal
        self.update_orthogonal_constraints()

    def insert_handle(self, index: int, handle: Handle) -> None:
        self._handles.insert(index, handle)

    def remove_handle(self, handle: Handle) -> None:
        self._handles.remove(handle)

    def insert_port(self, index: int, port: Port) -> None:
        self._ports.insert(index, port)

    def remove_port(self, port: Port) -> None:
        self._ports.remove(port)

    def _update_ports(self) -> None:
        """Update line ports.

        This destroys all previously created ports and should only be
        used when initializing the line.
        """
        assert len(self._handles) >= 2, "Not enough segments"
        handles = self._handles
        self._ports = [
            LinePort(h1.pos, h2.pos) for h1, h2 in zip(handles[:-1], handles[1:])
        ]

    def opposite(self, handle: Handle) -> Handle:
        """Given the handle of one end of the line, return the other end."""
        handles = self._handles
        if handle is handles[0]:
            return handles[-1]
        elif handle is handles[-1]:
            return handles[0]
        else:
            raise KeyError("Handle is not an end handle")

    def handles(self) -> Sequence[Handle]:
        """Return a list of handles owned by the item."""
        return self._handles

    def ports(self) -> Sequence[Port]:
        """Return list of ports."""
        return self._ports

    def point(self, x: float, y: float) -> float:
        """
        >>> a = Line()
        >>> a.handles()[1].pos = 25, 5
        >>> a._handles.append(a._create_handle((30, 30)))
        >>> a.point(-1, 0)
        1.0
        >>> f"{a.point(5, 4):.3f}"
        '2.942'
        >>> f"{a.point(29, 29):.3f}"
        '0.784'
        """
        hpos = [h.pos for h in self._handles]
        p = (x, y)
        distance, _point = min(
            distance_line_point(start, end, p)  # type: ignore[arg-type]
            for start, end in zip(hpos[:-1], hpos[1:])
        )
        return max(0.0, distance - self.fuzziness)

    def draw_head(self, context: DrawContext) -> None:
        """Default head drawer: move cursor to the first handle."""
        context.cairo.move_to(0, 0)

    def draw_tail(self, context: DrawContext) -> None:
        """Default tail drawer: draw line to the last handle."""
        context.cairo.line_to(0, 0)

    def draw(self, context: DrawContext) -> None:
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

        h0, h1 = self._handles[:2]
        p0, p1 = h0.pos, h1.pos
        head_angle = atan2(p1.y - p0.y, p1.x - p0.x)
        draw_line_end(self._handles[0].pos, head_angle, self.draw_head)

        for h in self._handles[1:-1]:
            cr.line_to(*h.pos)

        h1, h0 = self._handles[-2:]
        p1, p0 = h1.pos, h0.pos
        tail_angle = atan2(p1.y - p0.y, p1.x - p0.x)
        draw_line_end(self._handles[-1].pos, tail_angle, self.draw_tail)
        cr.stroke()
