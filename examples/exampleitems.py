"""Simple example items.

These items are used in various tests.
"""
from gaphas.connector import Handle
from gaphas.item import NW, Element, Item
from gaphas.util import path_ellipse, text_align, text_multiline


class Box(Element):
    """A Box has 4 handles (for a start):

    NW +---+ NE SW +---+ SE
    """

    def __init__(self, connections, width=10, height=10):
        """
        Initialize all connections.

        Args:
            self: (todo): write your description
            connections: (todo): write your description
            width: (int): write your description
            height: (int): write your description
        """
        super().__init__(connections, width, height)

    def draw(self, context):
        """
        Draws the context

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
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


class Text(Item):
    """Simple item showing some text on the canvas."""

    def __init__(self, text=None, plain=False, multiline=False, align_x=1, align_y=-1):
        """
        Initialize text.

        Args:
            self: (todo): write your description
            text: (str): write your description
            plain: (todo): write your description
            multiline: (bool): write your description
            align_x: (int): write your description
            align_y: (int): write your description
        """
        super().__init__()
        self.text = text is None and "Hello" or text
        self.plain = plain
        self.multiline = multiline
        self.align_x = align_x
        self.align_y = align_y

    def draw(self, context):
        """
        Draw text

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        cr = context.cairo
        if self.multiline:
            text_multiline(cr, 0, 0, self.text)
        elif self.plain:
            cr.show_text(self.text)
        else:
            text_align(cr, 0, 0, self.text, self.align_x, self.align_y)

    def point(self, pos):
        """
        Return the point at pos pos at pos pos.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        return 0


class Circle(Item):
    def __init__(self):
        """
        Initialize the underlying underlying handlers.

        Args:
            self: (todo): write your description
        """
        super().__init__()
        self._handles.extend((Handle(), Handle()))
        h1, h2 = self._handles
        h1.movable = False

    def _set_radius(self, r):
        """
        Set the radius of the rectangle.

        Args:
            self: (todo): write your description
            r: (todo): write your description
        """
        h1, h2 = self._handles
        h2.pos.x = r
        h2.pos.y = r

    def _get_radius(self):
        """
        Returns the radius of the rectangle.

        Args:
            self: (todo): write your description
        """
        h1, h2 = self._handles
        p1, p2 = h1.pos, h2.pos
        return ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5

    radius = property(_get_radius, _set_radius)

    def point(self, pos):
        """
        Returns the point at pos pos.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        h1, _ = self._handles
        p1 = h1.pos
        x, y = pos
        dist = ((x - p1.x) ** 2 + (y - p1.y) ** 2) ** 0.5
        return dist - self.radius

    def draw(self, context):
        """
        Draw a circle

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        cr = context.cairo
        path_ellipse(cr, 0, 0, 2 * self.radius, 2 * self.radius)
        cr.stroke()
