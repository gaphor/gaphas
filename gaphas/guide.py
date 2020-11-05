"""Module implements guides when moving items and handles around."""
from functools import reduce

from gaphas.aspect import (
    HandleInMotion,
    InMotion,
    ItemHandleInMotion,
    ItemInMotion,
    ItemPaintFocused,
    PaintFocused,
    singledispatch,
)
from gaphas.item import Element, Item, Line
from gaphas.view import GtkView


class ItemGuide:
    """Get edges on an item, on which we can align the items."""

    def __init__(self, item):
        """
        Initialize item

        Args:
            self: (todo): write your description
            item: (todo): write your description
        """
        self.item = item

    def horizontal(self):
        """Return horizontal edges (on y axis)"""
        return ()

    def vertical(self):
        """Return vertical edges (on x axis)"""
        return ()


Guide = singledispatch(ItemGuide)


@Guide.register(Element)
class ElementGuide(ItemGuide):
    """Guide to align Element items."""

    def horizontal(self):
        """
        The horizontal horizontal horizontal height.

        Args:
            self: (todo): write your description
        """
        y = self.item.height
        return (0, y / 2, y)

    def vertical(self):
        """
        Returns the vertical vertical width.

        Args:
            self: (todo): write your description
        """
        x = self.item.width
        return (0, x / 2, x)


@Guide.register(Line)
class LineGuide(ItemGuide):
    """Guide for orthogonal lines."""

    def horizontal(self):
        """
        Iterate horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal.

        Args:
            self: (todo): write your description
        """
        line = self.item
        if line.orthogonal:
            if line.horizontal:
                for i, h in enumerate(line.handles()):
                    if i % 2 == 1:
                        yield h.pos.y
            else:
                for i, h in enumerate(line.handles()):
                    if i % 2 == 0 and i > 0:
                        yield h.pos.y

    def vertical(self):
        """
        Return an iterator over vertical vertical vertical lines.

        Args:
            self: (todo): write your description
        """
        line = self.item
        if line.orthogonal:
            if line.horizontal:
                for i, h in enumerate(line.handles()):
                    if i % 2 == 0 and i > 0:
                        yield h.pos.x
            else:
                for i, h in enumerate(line.handles()):
                    if i % 2 == 1:
                        yield h.pos.x


class Guides:
    def __init__(self, v, h):
        """
        Initialize a new variable

        Args:
            self: (todo): write your description
            v: (int): write your description
            h: (int): write your description
        """
        self.v = v
        self.h = h

    def vertical(self):
        """
        Returns the vertical part of this node.

        Args:
            self: (todo): write your description
        """
        return self.v

    def horizontal(self):
        """
        The horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal horizontal.

        Args:
            self: (todo): write your description
        """
        return self.h


class GuideMixin:
    """Helper methods for guides."""

    MARGIN = 2

    item: Item
    view: GtkView

    def find_vertical_guides(self, item_vedges, pdx, height, excluded_items):
        """
        Finds the vertical vertices for the vertical item.

        Args:
            self: (todo): write your description
            item_vedges: (todo): write your description
            pdx: (todo): write your description
            height: (int): write your description
            excluded_items: (todo): write your description
        """
        view = self.view
        i2v = self.view.get_matrix_i2v
        margin = self.MARGIN
        items = [
            view.get_items_in_rectangle((x - margin, 0, margin * 2, height))
            for x in item_vedges
        ]

        try:
            guides = list(
                map(Guide, reduce(set.union, list(map(set, items))) - excluded_items)
            )
        except TypeError:
            guides = []

        vedges = set()
        for g in guides:
            for x in g.vertical():
                vedges.add(i2v(g.item).transform_point(x, 0)[0])
        dx, edges_x = self.find_closest(item_vedges, vedges)
        return dx, edges_x

    def find_horizontal_guides(self, item_hedges, pdy, width, excluded_items):
        """
        Find horizontal item_horides finder item_items.

        Args:
            self: (todo): write your description
            item_hedges: (int): write your description
            pdy: (todo): write your description
            width: (int): write your description
            excluded_items: (todo): write your description
        """
        view = self.view
        i2v = self.view.get_matrix_i2v
        margin = self.MARGIN
        items = [
            view.get_items_in_rectangle((0, y - margin, width, margin * 2))
            for y in item_hedges
        ]

        try:
            guides = list(
                map(Guide, reduce(set.union, list(map(set, items))) - excluded_items)
            )
        except TypeError:
            guides = []

        # Translate edges to canvas or view coordinates
        hedges = set()
        for g in guides:
            for y in g.horizontal():
                hedges.add(i2v(g.item).transform_point(0, y)[1])

        dy, edges_y = self.find_closest(item_hedges, hedges)
        return dy, edges_y

    def get_excluded_items(self):
        """Get a set of items excluded from guide calculation."""
        item = self.item
        view = self.view

        excluded_items = set(view.canvas.get_all_children(item))
        excluded_items.add(item)
        excluded_items.update(view.selection.selected_items)
        return excluded_items

    def get_view_dimensions(self):
        """
        Returns the dimensions of the view.

        Args:
            self: (todo): write your description
        """
        try:
            allocation = self.view.get_allocation()
        except AttributeError:
            return 0, 0
        return allocation.width, allocation.height

    def queue_draw_guides(self):
        """
        Queue all the tiles in the figure.

        Args:
            self: (todo): write your description
        """
        view = self.view
        try:
            guides = view.guides
        except AttributeError:
            return

        w, h = self.get_view_dimensions()

        for x in guides.vertical():
            view.queue_redraw()
        for y in guides.horizontal():
            view.queue_redraw()

    def find_closest(self, item_edges, edges):
        """
        Find closest item in the closest item.

        Args:
            self: (todo): write your description
            item_edges: (todo): write your description
            edges: (list): write your description
        """
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
        if min_d <= self.MARGIN:
            return delta, closest
        else:
            return 0, ()


@InMotion.register(Item)
class GuidedItemInMotion(GuideMixin, ItemInMotion):
    """Move the item, lock position on any element that's located at the same
    location."""

    def move(self, pos):
        """
        Moves the view.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        item = self.item
        view = self.view

        transform = view.get_matrix_i2v(item).transform_point
        w, h = self.get_view_dimensions()

        px, py = pos
        pdx, pdy = px - self.last_x, py - self.last_y

        excluded_items = self.get_excluded_items()

        item_guide = Guide(item)
        item_vedges = [transform(x, 0)[0] + pdx for x in item_guide.vertical()]
        dx, edges_x = self.find_vertical_guides(item_vedges, pdx, h, excluded_items)

        item_hedges = [transform(0, y)[1] + pdy for y in item_guide.horizontal()]
        dy, edges_y = self.find_horizontal_guides(item_hedges, pdy, w, excluded_items)

        newpos = px + dx, py + dy

        # Call super class, with new position
        sink = super().move(newpos)

        self.queue_draw_guides()

        view.guides = Guides(edges_x, edges_y)

        self.queue_draw_guides()

        return sink

    def stop_move(self):
        """
        Stops the figure.

        Args:
            self: (todo): write your description
        """
        self.queue_draw_guides()
        try:
            del self.view.guides
        except AttributeError:
            # No problem if guides do not exist.
            pass


@HandleInMotion.register(Item)
class GuidedItemHandleInMotion(GuideMixin, ItemHandleInMotion):
    """Move a handle and lock the position of other elements.

    Locks the position of another element that's located at the same
    position.
    """

    def move(self, pos):
        """
        Called when the : meth :. wx.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """

        sink = super().move(pos)

        if not sink:
            item = self.item
            view = self.view
            canvas = view.canvas
            x, y = pos
            v2i = view.get_matrix_v2i(item)

            excluded_items = self.get_excluded_items()

            w, h = self.get_view_dimensions()

            dx, edges_x = self.find_vertical_guides((x,), 0, h, excluded_items)

            dy, edges_y = self.find_horizontal_guides((y,), 0, w, excluded_items)

            newpos = x + dx, y + dy

            x, y = v2i.transform_point(*newpos)

            self.handle.pos = (x, y)
            # super(GuidedItemHandleInMotion, self).move(newpos)

            self.queue_draw_guides()

            view.guides = Guides(edges_x, edges_y)

            self.queue_draw_guides()

            canvas.request_update(item)

    def stop_move(self):
        """
        Stops the figure.

        Args:
            self: (todo): write your description
        """
        self.queue_draw_guides()
        try:
            del self.view.guides
        except AttributeError:
            # No problem if guides do not exist.
            pass


@PaintFocused.register(Item)
class GuidePainter(ItemPaintFocused):
    def paint(self, cr):
        """
        Paint the image.

        Args:
            self: (todo): write your description
            cr: (todo): write your description
        """
        try:
            guides = self.view.guides
        except AttributeError:
            return

        view = self.view
        allocation = view.get_allocation()
        w, h = allocation.width, allocation.height

        cr.save()
        try:
            cr.set_line_width(1)
            cr.set_source_rgba(0.0, 0.0, 1.0, 0.6)
            for g in guides.vertical():
                cr.move_to(g, 0)
                cr.line_to(g, h)
                cr.stroke()
            for g in guides.horizontal():
                cr.move_to(0, g)
                cr.line_to(w, g)
                cr.stroke()
        finally:
            cr.restore()
