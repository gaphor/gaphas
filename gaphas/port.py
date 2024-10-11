"""Basic connectors such as Ports and Handles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gaphas.constraint import Constraint, LineConstraint, PositionConstraint
from gaphas.geometry import distance_line_point, distance_point_point
from gaphas.handle import Handle
from gaphas.position import MatrixProjection, Position
from gaphas.solver import MultiConstraint
from gaphas.types import Pos, SupportsFloatPos

if TYPE_CHECKING:
    from gaphas.item import Item


class Port:
    """Port connectable part of an item.

    The Item's handle connects to a port.
    """

    def __init__(self) -> None:
        super().__init__()

        self._connectable = True

    def _set_connectable(self, connectable: bool) -> None:
        self._connectable = connectable

    connectable = property(lambda s: s._connectable, _set_connectable)

    def glue(self, pos: SupportsFloatPos) -> tuple[Pos, float]:
        """Get glue point on the port and distance to the port."""
        raise NotImplementedError("Glue method not implemented")

    def constraint(self, item: Item, handle: Handle, glue_item: Item) -> Constraint:
        """Create connection constraint between item's handle and glue item."""
        raise NotImplementedError("Constraint method not implemented")


class LinePort(Port):
    """Port defined as a line between two handles."""

    def __init__(self, start: Position, end: Position) -> None:
        super().__init__()

        self.start = start
        self.end = end

    def glue(self, pos: SupportsFloatPos) -> tuple[Pos, float]:
        """Get glue point on the port and distance to the port.

        >>> p1, p2 = (0.0, 0.0), (100.0, 100.0)
        >>> port = LinePort(p1, p2)
        >>> port.glue((50, 50))
        ((50.0, 50.0), 0.0)
        >>> port.glue((0, 10))
        ((5.0, 5.0), 7.0710678118654755)
        """
        d, pl = distance_line_point(
            self.start.tuple(), self.end.tuple(), (float(pos[0]), float(pos[1]))
        )
        return pl, d

    def constraint(self, item: Item, handle: Handle, glue_item: Item) -> Constraint:
        """Create connection line constraint between item's handle and the
        port."""
        start = MatrixProjection(self.start, glue_item.matrix_i2c)
        end = MatrixProjection(self.end, glue_item.matrix_i2c)
        point = MatrixProjection(handle.pos, item.matrix_i2c)
        line = LineConstraint((start.pos, end.pos), point.pos)
        return MultiConstraint(start, end, point, line)


class PointPort(Port):
    """Port defined as a point."""

    def __init__(self, point: Position) -> None:
        super().__init__()
        self.point = point

    def glue(self, pos: SupportsFloatPos) -> tuple[Pos, float]:
        """Get glue point on the port and distance to the port.

        >>> h = Handle((10, 10))
        >>> port = PointPort(h.pos)
        >>> port.glue((10, 0))
        (<Position object on (10, 10)>, 10.0)
        """
        point: tuple[float, float] = self.point.pos  # type: ignore[assignment]
        d = distance_point_point(point, (float(pos[0]), float(pos[1])))
        return point, d

    def constraint(
        self, item: Item, handle: Handle, glue_item: Item
    ) -> MultiConstraint:
        """Return connection position constraint between item's handle and the
        port."""
        origin = MatrixProjection(self.point, glue_item.matrix_i2c)
        point = MatrixProjection(handle.pos, item.matrix_i2c)
        c = PositionConstraint(origin.pos, point.pos)
        return MultiConstraint(origin, point, c)
