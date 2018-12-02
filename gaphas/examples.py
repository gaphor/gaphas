"""
Simple example items.
These items are used in various tests.
"""
from __future__ import absolute_import
from __future__ import division

from gaphas.connector import Handle, PointPort, LinePort, Position
from gaphas.item import Element, Item, NW, NE, SW, SE
from gaphas.solver import WEAK
from .util import text_align, text_multiline, path_ellipse


class Box(Element):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Box, self).__init__(width, height)

    def draw(self, context):
        c = context.cairo
        nw = self._handles[NW].pos
        c.rectangle(nw.x, nw.y, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(0.8, 0.8, 1, 0.8)
        else:
            c.set_source_rgba(1, 1, 1, 0.8)
        c.fill_preserve()
        c.set_source_rgb(0, 0, 0.8)
        c.stroke()


class PortoBox(Box):
    """
    Box item with few flavours of port(o)s.

    Default box ports are disabled. Three, non-default connectable
    ports are created (represented by ``x`` on the picture).

    - point port on the east edge, movable with a handle
    - static point port in the middle of the south edge
    - line port from north-west to south east corner

         NW +--------+ NE
            |xx      |
            |  xx    |x
            |    xx  |
            |      xx|
         SW +--------+ SE
                x
    """

    def __init__(self, width=10, height=10):
        super(PortoBox, self).__init__(width, height)

        # disable default ports
        for p in self._ports:
            p.connectable = False

        nw = self._handles[NW]
        sw = self._handles[SW]
        ne = self._handles[NE]
        se = self._handles[SE]

        # handle for movable port
        self._hm = Handle(strength=WEAK)
        self._hm.pos = width, height / 2.0
        self._handles.append(self._hm)

        # movable port
        self._ports.append(PointPort(self._hm.pos))

        # keep movable port at right edge
        self.constraint(vertical=(self._hm.pos, ne.pos), delta=10)
        self.constraint(above=(ne.pos, self._hm.pos))
        self.constraint(above=(self._hm.pos, se.pos))

        # static point port
        self._sport = PointPort(Position((width / 2.0, height)))
        l = sw.pos, se.pos
        self.constraint(line=(self._sport.point, l))
        self._ports.append(self._sport)

        # line port
        self._lport = LinePort(nw.pos, se.pos)
        self._ports.append(self._lport)

    def draw(self, context):
        super(PortoBox, self).draw(context)
        c = context.cairo

        if context.hovered:
            c.set_source_rgba(0.0, 0.8, 0, 0.8)
        else:
            c.set_source_rgba(0.9, 0.0, 0.0, 0.8)

        # draw movable port
        x, y = self._hm.pos
        c.rectangle(x - 20, y - 5, 20, 10)
        c.rectangle(x - 1, y - 1, 2, 2)

        # draw static port
        x, y = self._sport.point
        c.rectangle(x - 2, y - 2, 4, 4)

        c.fill_preserve()

        # draw line port
        x1, y1 = self._lport.start
        x2, y2 = self._lport.end
        c.move_to(x1, y1)
        c.line_to(x2, y2)

        c.set_source_rgb(0, 0, 0.8)
        c.stroke()


class Text(Item):
    """
    Simple item showing some text on the canvas.
    """

    def __init__(self, text=None, plain=False, multiline=False, align_x=1, align_y=-1):
        super(Text, self).__init__()
        self.text = text is None and "Hello" or text
        self.plain = plain
        self.multiline = multiline
        self.align_x = align_x
        self.align_y = align_y

    def draw(self, context):
        cr = context.cairo
        if self.multiline:
            text_multiline(cr, 0, 0, self.text)
        elif self.plain:
            cr.show_text(self.text)
        else:
            text_align(cr, 0, 0, self.text, self.align_x, self.align_y)

    def point(self, pos):
        return 0


class FatLine(Item):
    """
    Simple, vertical line with two handles.

    todo: rectangle port instead of line port would be nicer
    """

    def __init__(self):
        super(FatLine, self).__init__()
        self._handles.extend((Handle(), Handle()))

        h1, h2 = self._handles

        self._ports.append(LinePort(h1.pos, h2.pos))

        self.constraint(vertical=(h1.pos, h2.pos))
        self.constraint(above=(h1.pos, h2.pos), delta=20)

    def _set_height(self, height):
        h1, h2 = self._handles
        h2.pos.y = height

    def _get_height(self):
        h1, h2 = self._handles
        return h2.pos.y

    height = property(_get_height, _set_height)

    def draw(self, context):
        cr = context.cairo
        cr.set_line_width(10)
        h1, h2 = self.handles()
        cr.move_to(0, 0)
        cr.line_to(0, self.height)
        cr.stroke()


class Circle(Item):
    def __init__(self):
        super(Circle, self).__init__()
        self._handles.extend((Handle(), Handle()))

    def _set_radius(self, r):
        h1, h2 = self._handles
        h2.pos.x = r
        h2.pos.y = r

    def _get_radius(self):
        h1, h2 = self._handles
        p1, p2 = h1.pos, h2.pos
        return ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5

    radius = property(_get_radius, _set_radius)

    def setup_canvas(self):
        super(Circle, self).setup_canvas()
        h1, h2 = self._handles
        h1.movable = False

    def point(self, pos):
        h1, _ = self._handles
        p1 = h1.pos
        x, y = pos
        dist = ((x - p1.x) ** 2 + (y - p1.y) ** 2) ** 0.5
        return dist - self.radius

    def draw(self, context):
        cr = context.cairo
        path_ellipse(cr, 0, 0, 2 * self.radius, 2 * self.radius)
        cr.stroke()


# vim: sw=4:et:ai
