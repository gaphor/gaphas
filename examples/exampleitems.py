"""Simple example items.

These items are used in various tests.
"""
from gaphas.connector import Handle
from gaphas.item import NW, Element, Matrices, Updateable
from gaphas.util import path_ellipse, text_align, text_multiline


class Box(Element):
    """A Box has 4 handles (for a start):

    NW +---+ NE SW +---+ SE
    """

    def __init__(self, connections, width=10, height=10):
        super().__init__(connections, width, height)

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


class Text(Matrices, Updateable):
    """Simple item showing some text on the canvas."""

    def __init__(self, text=None, plain=False, multiline=False, align_x=1, align_y=-1):
        super().__init__()
        self.text = text is None and "Hello" or text
        self.plain = plain
        self.multiline = multiline
        self.align_x = align_x
        self.align_y = align_y

    def handles(self):
        return []

    def ports(self):
        return []

    def point(self, x, y):
        return 0

    def draw(self, context):
        cr = context.cairo
        if self.multiline:
            text_multiline(cr, 0, 0, self.text)
        elif self.plain:
            cr.show_text(self.text)
        else:
            text_align(cr, 0, 0, self.text, self.align_x, self.align_y)


class Circle(Matrices, Updateable):
    def __init__(self):
        super().__init__()
        self._handles = [Handle(), Handle()]
        h1, h2 = self._handles
        h1.movable = False

    @property
    def radius(self):
        h1, h2 = self._handles
        p1, p2 = h1.pos, h2.pos
        return ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5

    @radius.setter
    def radius(self, r):
        h1, h2 = self._handles
        h2.pos.x = r
        h2.pos.y = r

    def handles(self):
        return self._handles

    def ports(self):
        return []

    def point(self, x, y):
        h1, _ = self._handles
        p1 = h1.pos
        dist = ((x - p1.x) ** 2 + (y - p1.y) ** 2) ** 0.5
        return dist - self.radius

    def draw(self, context):
        cr = context.cairo
        path_ellipse(cr, 0, 0, 2 * self.radius, 2 * self.radius)
        cr.stroke()
