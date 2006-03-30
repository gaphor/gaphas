"""Simple example items.
These items are used in various tests.
"""

from item import Handle, Item
from solver import solvable

class Box(Item):

    _width = solvable()
    _height = solvable()

    def __init__(self):
        super(Box, self).__init__()
        self._width = 10
        self._height = 10
        self._handles = [Handle(0, 0), Handle(self._width, 0),
                         Handle(0, self._height), Handle(self._width, self._height)]

    def handles(self):
        return iter(self._handles)

    def update(self, context):
        self._handles[1].x = self._handles[3].x = self._width
        self._handles[2].y = self._handles[3].y = self._height

    def draw(self, context):
        print 'Box.draw', self
        c = context.cairo
        c.rectangle(0,0, self._width, self._height)
        if context.hovered:
            c.set_source_rgba(.8,.8,1, 1)
        else:
            c.set_source_rgba(1,1,1, 1)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()
        context.draw_children()


class Text(Item):
    def __init__(self):
        super(Text, self).__init__()


    def draw(self, context):
        print 'Text.draw', self
        c = context.cairo
        c.show_text('Hello')
        context.draw_children()

# vim: sw=4:et:ai
