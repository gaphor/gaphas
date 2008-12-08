"""
Simple example items.
These items are used in various tests.
"""

__version__ = "$Revision$"
# $HeadURL$

from gaphas.item import Element, Item, NW, NE,SW, SE
from gaphas.connector import Handle, PointPort
from gaphas.constraint import LessThanConstraint, EqualsConstraint, \
    BalanceConstraint
from gaphas.solver import solvable, WEAK
import tool
from util import text_extents, text_align, text_multiline, path_ellipse
from cairo import Matrix

class Box(Element):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Box, self).__init__(width, height)

    def draw(self, context):
        #print 'Box.draw', self
        c = context.cairo
        nw = self._handles[NW]
        c.rectangle(nw.x, nw.y, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(.8,.8,1, .8)
        else:
            c.set_source_rgba(1,1,1, .8)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()


class BoxX(Box):
    """
    It is a Box but with additional port (see "x" below).

     NW +--------+ NE
        |        |
        |        |
        |        |x
        |        |
     SW +--------+ SE
    """
    def __init__(self, width=10, height=10):
        super(BoxX, self).__init__(width, height)
        self._hx = Handle(strength=WEAK)
        #self._hx.movable = False
        #self._hx.visible = False
        self._handles.append(self._hx)
        # define 'x' port
        self._ports.append(PointPort(self._hx.pos))

        # keep hx handle at right edge, at 80% of height of the box
        ne = self._handles[NE]
        se = self._handles[SE]
        hxc1 = EqualsConstraint(ne.x, self._hx.x, delta=10)
        #hxc2 = BalanceConstraint(band=(ne.y, se.y), v=self._hx.y, balance=0.8)
        self._constraints.append(hxc1)
        #self._constraints.append(hxc2)


    def draw(self, context):
        super(BoxX, self).draw(context)
        c = context.cairo

        # draw 'x' port
        hx = self._hx
        c.rectangle(hx.x - 20 , hx.y - 5, 20, 10)
        c.rectangle(hx.x - 1 , hx.y - 1, 2, 2)
        if context.hovered:
            c.set_source_rgba(.0, .8, 0, .8)
        else:
            c.set_source_rgba(.9, .0, .0, .8)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()




class Text(Item):
    """
    Simple item showing some text on the canvas.
    """

    def __init__(self, text=None, plain=False, multiline=False, align_x=1, align_y=-1):
        super(Text, self).__init__()
        self.text = text is None and 'Hello' or text
        self.plain = plain
        self.multiline = multiline
        self.align_x = align_x
        self.align_y = align_y

    def draw(self, context):
        #print 'Text.draw', self
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
    def __init__(self):
        super(FatLine, self).__init__()
        self._handles.extend((Handle(), Handle()))

        h1, h2 = self._handles
        cons = self._constraints
        cons.append(EqualsConstraint(a=h1.x, b=h2.x))
        cons.append(LessThanConstraint(smaller=h1.y, bigger=h2.y, delta=20))


    def _set_height(self, height):
        h1, h2 = self._handles
        h2.y = height


    def _get_height(self):
        h1, h2 = self._handles
        return h2.y


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
        h2.x = r
        h2.y = r


    def _get_radius(self):
        h1, h2 = self._handles
        return ((h2.x - h1.x) ** 2 + (h2.y - h1.y) ** 2) ** 0.5

    radius = property(_get_radius, _set_radius)


    def setup_canvas(self):
        super(Circle, self).setup_canvas()
        h1, h2 = self._handles
        h1.movable = False


    def draw(self, context):
        cr = context.cairo
        path_ellipse(cr, 0, 0, 2 * self.radius, 2 * self.radius)
        cr.stroke()



# vim: sw=4:et:ai
