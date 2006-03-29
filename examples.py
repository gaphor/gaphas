"""Simple example items.
These items are used in various tests.
"""

from item import Handle, Item

class Box(Item):
    def __init__(self):
        super(Box, self).__init__()
        self._width = 10
        self._height = 10
        self._handles = [Handle(0, 0)]

    def handles(self):
        return iter(self._handles)

    def update(self, context):
        self._handles[0].x = self._width
        self._handles[0].y = self._height

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

