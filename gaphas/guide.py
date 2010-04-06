"""
Module implements guides when moving items and handles around.
"""

from simplegeneric import generic
from gaphas.aspect import InMotion, HandleInMotion, PaintFocused
from gaphas.aspect import ItemInMotion, ItemHandleInMotion, ItemPaintFocused
from gaphas.item import Item, Element, SE


class ItemGuide(object):
    """
    Get edges on an item, on which we can align the items.
    """

    def __init__(self, item):
        self.item = item

    def horizontal(self):
        """
        Return horizontal edges (on y axis)
        """
        return ()

    def vertical(self):
        """
        Return vertical edges (on x axis)
        """
        return ()


Guide = generic(ItemGuide)


@Guide.when_type(Element)
class ElementGuide(ItemGuide):

    def horizontal(self):
        y = self.item.height
        return (0, y)

    def vertical(self):
        x = self.item.width
        return (0, x)

# TODO: Create guides on orthogonal lines

class Guides(object):

    def __init__(self, v, h):
        self.v = v
        self.h = h

    def vertical(self):
        return self.v

    def horizontal(self):
        return self.h


@InMotion.when_type(Item)
class GuidedItemInMotion(ItemInMotion):
    """
    Move the item, lock position on any element that's located at the same
    location.
    """
    MARGIN = 2

    def move(self, pos):
        margin = self.MARGIN
        item = self.item
        view = self.view

        allocation = view.allocation
        w, h = allocation.width, allocation.height

        px, py = pos
        pdx, pdy = px - self.last_x, py - self.last_y
        
        i2v = self.view.get_matrix_i2v

        children_and_self = set(view.canvas.get_children(item))
        children_and_self.add(item)

        item_guide = Guide(item)
        tp = i2v(item).transform_point

        # Vertical:

        item_vedges = [tp(x, 0)[0] + pdx for x in item_guide.vertical()]
        items = []
        for x in item_vedges:
            items.append(view.get_items_in_rectangle((x - margin, 0, margin*2, h)))
        try:
            guides = map(Guide, reduce(set.union, map(set, items)) - children_and_self)
        except TypeError:
            guides = []

        vedges = set()
        for g in guides:
            for x in g.vertical():
                vedges.add(i2v(g.item).transform_point(x, 0)[0])

        dx, edges_x = self.find_closest(item_vedges, vedges)

        # Horizontal:

        item_hedges = [tp(0, y)[1] + pdy for y in item_guide.horizontal()]
        items = []
        for y in item_hedges:
            items.append(view.get_items_in_rectangle((0, y - margin, w, margin*2)))
        try:
            guides = map(Guide, reduce(set.union, map(set, items)) - children_and_self)
        except TypeError:
            guides = []

        # Translate edges to canvas or view coordinates
        hedges = set()
        for g in guides:
            for y in g.horizontal():
                hedges.add(i2v(g.item).transform_point(0, y)[1])

        dy, edges_y = self.find_closest(item_hedges, hedges)

        newpos = pos[0] + dx, pos[1] + dy

        # Call super class, with new position
        super(GuidedItemInMotion, self).move(newpos)

        self.queue_draw_guides()

        view.guides = Guides(edges_x, edges_y)

        self.queue_draw_guides()


    def stop_move(self):
        self.queue_draw_guides()
        try:
            del self.view.guides
        except AttributeError:
            # No problem if guides do not exist.
            pass


    def queue_draw_guides(self):
        view = self.view
        try:
            guides = view.guides
        except AttributeError:
            return

        allocation = view.allocation
        w, h = allocation.width, allocation.height

        for x in guides.vertical():
            view.queue_draw_area(x-1, 0, x+2, h)
        for y in guides.horizontal():
            view.queue_draw_area(0, y-1, w, y+2)


    def find_closest(self, item_edges, edges):
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


@PaintFocused.when_type(Item)
class GuidePainter(ItemPaintFocused):

    def paint(self, context):
        try:
            guides = self.view.guides
        except AttributeError:
            return
        
        cr = context.cairo
        view = self.view
        allocation = view.allocation
        w, h = allocation.width, allocation.height

        cr.save()
        try:
            cr.set_line_width(1)
            cr.set_source_rgba(0.0, 0.0, 1.0, 0.6)
            #cr.set_antialias(ANTIALIAS_NONE)
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

# vim:sw=4:et:ai
