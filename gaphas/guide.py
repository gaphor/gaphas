"""Module implements guides when moving items and handles around."""

from __future__ import annotations

from dataclasses import dataclass
from functools import singledispatch
from itertools import chain
from typing import TYPE_CHECKING, Iterable, SupportsFloat

from gaphas.canvas import all_children
from gaphas.connector import Handle
from gaphas.handlemove import HandleMove, ItemHandleMove
from gaphas.item import Element, Item, Line
from gaphas.move import ItemMove, Move
from gaphas.types import Pos

if TYPE_CHECKING:
    from gaphas.view import GtkView


class ItemGuide:
    """Get edges on an item, on which we can align the items."""

    def __init__(self, item: Item, handle: Handle | None = None):
        self.item = item
        self.handle = handle

    def horizontal(self) -> Iterable[SupportsFloat]:
        """Return horizontal edges (on y axis) in item coordinates."""
        return ()

    def vertical(self) -> Iterable[SupportsFloat]:
        """Return vertical edges (on x axis) in item coordinates."""
        return ()


Guide = singledispatch(ItemGuide)


@Guide.register(Element)
class ElementGuide(ItemGuide):
    """Guide to align Element items."""

    def horizontal(self) -> Iterable[SupportsFloat]:
        element = self.item
        assert isinstance(element, Element)
        if self.handle in element.handles():
            return ()
        y = element.handles()[0].pos.y
        h = element.height
        return [y, y + h / 2, y + h]

    def vertical(self) -> Iterable[SupportsFloat]:
        element = self.item
        assert isinstance(element, Element)
        if self.handle in element.handles():
            return ()
        x = element.handles()[0].pos.x
        w = element.width
        return [x, x + w / 2, x + w]


@Guide.register(Line)
class LineGuide(ItemGuide):
    """Guide for orthogonal lines."""

    def horizontal(self) -> Iterable[SupportsFloat]:
        line = self.item
        assert isinstance(line, Line)
        if not line.orthogonal or self.handle not in line.handles():
            yield from (h.pos.y for h in line.handles() if h is not self.handle)

    def vertical(self) -> Iterable[SupportsFloat]:
        line = self.item
        assert isinstance(line, Line)
        if not line.orthogonal or self.handle not in line.handles():
            yield from (h.pos.x for h in line.handles() if h is not self.handle)


@dataclass(frozen=True)
class Guides:
    vertical: list[float]
    horizontal: list[float]


MARGIN = 4


def find_vertical_guides(view, handle, item_vedges, height, excluded_items, margin):
    items = (
        set(
            chain.from_iterable(
                view.get_items_in_rectangle((x - margin, 0, margin * 2, height))
                for x in item_vedges
            )
        )
        - excluded_items
    )
    guides = (Guide(item, handle) for item in items)
    i2v = view.get_matrix_i2v
    vedges = {
        i2v(g.item).transform_point(x, 0)[0] for g in guides for x in g.vertical()
    }
    dx, edges_x = find_closest(item_vedges, vedges)
    return dx, edges_x


def find_horizontal_guides(view, handle, item_hedges, width, excluded_items, margin):
    items = (
        set(
            chain.from_iterable(
                view.get_items_in_rectangle((0, y - margin, width, margin * 2))
                for y in item_hedges
            )
        )
        - excluded_items
    )
    guides = (Guide(item, handle) for item in items)
    i2v = view.get_matrix_i2v
    hedges = {
        i2v(g.item).transform_point(0, y)[1] for g in guides for y in g.horizontal()
    }
    dy, edges_y = find_closest(item_hedges, hedges)
    return dy, edges_y


def get_excluded_items(view, item):
    """Get a set of items excluded from guide calculation."""
    assert view.model

    excluded_items = set(all_children(view.model, item))
    excluded_items.add(item)
    excluded_items.update(view.selection.selected_items)
    return excluded_items


def find_closest(item_edges, edges, margin=MARGIN):
    delta = 0
    min_d = 1000
    closest = []
    for e in edges:
        for ie in item_edges:
            d = abs(e - ie)
            if d < min_d:
                min_d = d
                delta = e - ie
                closest = [e]
            elif d == min_d:
                closest.append(e)

    return (delta, closest) if min_d <= margin else (0, ())


def update_guides(view, handle, vedges, hedges, excluded_items=frozenset()):
    dx, edges_x = find_vertical_guides(
        view, handle, vedges, view.get_height(), excluded_items, MARGIN
    )
    dy, edges_y = find_horizontal_guides(
        view, handle, hedges, view.get_width(), excluded_items, MARGIN
    )

    view.guides = Guides(edges_x, edges_y)

    view.update_back_buffer()

    return dx, dy


def reset_guides(view):
    try:
        del view.guides
    except AttributeError:
        # No problem if guides do not exist.
        pass
    else:
        view.update_back_buffer()


class GuidedItemMoveMixin:
    """Move the item, lock position on any element that's located at the same
    location."""

    view: GtkView
    item: Item
    last_x: float
    last_y: float

    def move(self, pos: Pos) -> None:
        item = self.item
        view = self.view

        px, py = pos
        pdx, pdy = px - self.last_x, py - self.last_y

        transform = view.get_matrix_i2v(item).transform_point
        item_guide = Guide(item)
        item_vedges = [transform(x, 0)[0] + pdx for x in item_guide.vertical()]
        item_hedges = [transform(0, y)[1] + pdy for y in item_guide.horizontal()]

        excluded_items = get_excluded_items(view, item)
        dx, dy = update_guides(view, None, item_vedges, item_hedges, excluded_items)

        # Call super class, with new position
        super().move((pos[0] + dx, pos[1] + dy))  # type: ignore[misc]

    def stop_move(self, pos: Pos) -> None:
        super().stop_move(pos)  # type: ignore[misc]
        reset_guides(self.view)


@Move.register(Element)
class GuidedItemMove(GuidedItemMoveMixin, ItemMove):
    pass


class GuidedItemHandleMoveMixin:
    """Move a handle and lock the position of other elements.

    Locks the position of another element that's located at the same
    position.
    """

    view: GtkView
    item: Item
    handle: Handle

    def move(self, pos: Pos) -> None:
        super().move(pos)  # type: ignore[misc]

        item = self.item
        view = self.view
        model = view.model
        assert model

        x, y = pos
        dx, dy = update_guides(view, self.handle, (x,), (y,))

        self.handle.pos = view.get_matrix_v2i(item).transform_point(x + dx, y + dy)
        model.request_update(item)

    def stop_move(self, pos: Pos) -> None:
        super().stop_move(pos)  # type: ignore[misc]
        reset_guides(self.view)


@HandleMove.register(Element)
class GuidedElementHandleMove(GuidedItemHandleMoveMixin, ItemHandleMove):
    pass


@HandleMove.register(Line)
class GuidedLineHandleMove(GuidedItemHandleMoveMixin, ItemHandleMove):
    pass


class GuidePainter:
    def __init__(self, view: GtkView):
        self.view = view

    def paint(self, _items, cr):
        try:
            guides = self.view.guides
        except AttributeError:
            return

        view = self.view

        cr.save()
        try:
            cr.identity_matrix()
            cr.set_line_width(1)
            cr.set_source_rgba(0.0, 0.0, 1.0, 0.6)
            for g in guides.vertical:
                cr.move_to(g, 0)
                cr.line_to(g, view.get_height())
                cr.stroke()
            for g in guides.horizontal:
                cr.move_to(0, g)
                cr.line_to(view.get_width(), g)
                cr.stroke()
        finally:
            cr.restore()
