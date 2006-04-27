"""Simple example items.
These items are used in various tests.
"""

__version__ = "$Revision$"
# $HeadURL$

from item import Handle, Element, Item
from item import NW, NE,SW, SE
from solver import solvable


class Box(Element):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """

    def __init__(self, width=10, height=10):
        super(Box, self).__init__()

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
        context.draw_children()


class Text(Item):

    def __init__(self):
        super(Text, self).__init__()

    def draw(self, context):
        #print 'Text.draw', self
        c = context.cairo
        c.show_text('Hello')
        context.draw_children()

    def point(self, x, y):
        return 0

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
