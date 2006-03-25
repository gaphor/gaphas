"""Simple example items.
These items are used in various tests.
"""

from item import Handle, Item

class Box(Item):
    def __init__(self):
        print 'Box.__init__'
        super(Box, self).__init__()
        self._width = 10
        self._height = 10

    def draw(self, context):
        print 'Box.draw'
        c = context.cairo
        c.rectangle(0,0, self._width, self._height)
        c.set_source_rgb(0,0,0)
        c.stroke()
        context.draw_children()
