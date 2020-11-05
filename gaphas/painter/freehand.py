"""Cairo context using Steve Hanov's freehand drawing code.

    # Crazyline. By Steve Hanov, 2008 Released to the public domain.

    # The idea is to draw a curve, setting two control points at
    # random close to each side of the line. The longer the line, the
    # sloppier it's drawn.

See: http://stevehanov.ca/blog/index.php?id=33 and
     http://stevehanov.ca/blog/index.php?id=93
"""
from math import sqrt
from random import Random
from typing import Sequence

from gaphas.item import Item
from gaphas.painter.painter import ItemPainterType


class FreeHandCairoContext:

    KAPPA = 0.5522847498

    def __init__(self, cr, sloppiness=0.5):
        """Create context with given sloppiness. Range [0..2.0] gives
        acceptable results.

        * Draftsman: 0.0
        * Artist: 0.25
        * Cartoonist: 0.5
        * Child: 1.0
        * Drunk: 2.0
        """
        self.cr = cr
        self.sloppiness = sloppiness  # In range 0.0 .. 2.0

    def __getattr__(self, key):
        """
        Return the value from the cache.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        return getattr(self.cr, key)

    def line_to(self, x, y):
        """
        Draw a line on a line.

        Args:
            self: (todo): write your description
            x: (todo): write your description
            y: (todo): write your description
        """
        cr = self.cr
        sloppiness = self.sloppiness
        from_x, from_y = cr.get_current_point()

        # calculate the length of the line.
        length = sqrt((x - from_x) * (x - from_x) + (y - from_y) * (y - from_y))

        # This offset determines how sloppy the line is drawn. It depends on
        # the length, but maxes out at 20.
        offset = length / 10 * sloppiness
        if offset > 20:
            offset = 20

        dev_x, dev_y = cr.user_to_device(x, y)
        rand = Random((from_x, from_y, dev_x, dev_y, length, offset)).random

        # Overshoot the destination a little, as one might if drawing with a pen.
        to_x = x + sloppiness * rand() * offset / 4
        to_y = y + sloppiness * rand() * offset / 4

        # t1 and t2 are coordinates of a line shifted under or to the right of
        # our original.
        t1_x = from_x + offset
        t1_y = from_y + offset
        t2_x = to_x + offset
        t2_y = to_y + offset

        # create a control point at random along our shifted line.
        r = rand()
        control1_x = t1_x + r * (t2_x - t1_x)
        control1_y = t1_y + r * (t2_y - t1_y)

        # now make t1 and t2 the coordinates of our line shifted above
        # and to the left of the original.

        t1_x = from_x - offset
        t2_x = to_x - offset
        t1_y = from_y - offset
        t2_y = to_y - offset

        # create a second control point at random along the shifted line.
        r = rand()
        control2_x = t1_x + r * (t2_x - t1_x)
        control2_y = t1_y + r * (t2_y - t1_y)

        # draw the line!
        cr.curve_to(control1_x, control1_y, control2_x, control2_y, to_x, to_y)

    def rel_line_to(self, dx, dy):
        """
        Relative relative point

        Args:
            self: (todo): write your description
            dx: (todo): write your description
            dy: (todo): write your description
        """
        cr = self.cr
        from_x, from_y = cr.get_current_point()
        self.line_to(from_x + dx, from_y + dy)

    def curve_to(self, x1, y1, x2, y2, x3, y3):
        """
        Convenience function x1 and b.

        Args:
            self: (todo): write your description
            x1: (todo): write your description
            y1: (todo): write your description
            x2: (todo): write your description
            y2: (todo): write your description
            x3: (todo): write your description
            y3: (todo): write your description
        """
        cr = self.cr
        from_x, from_y = cr.get_current_point()

        dev_x, dev_y = cr.user_to_device(x3, y3)
        rand = Random((from_x, from_y, dev_x, dev_y, x1, y1, x2, y2, x3, y3)).random

        r = rand()
        c1_x = from_x + r * (x1 - from_x)
        c1_y = from_y + r * (y1 - from_y)

        r = rand()
        c2_x = x3 + r * (x2 - x3)
        c2_y = y3 + r * (y2 - y3)

        cr.curve_to(c1_x, c1_y, c2_x, c2_y, x3, y3)

    def rel_curve_to(self, dx1, dy1, dx2, dy2, dx3, dy3):
        """
        : param dx_curve.

        Args:
            self: (todo): write your description
            dx1: (todo): write your description
            dy1: (todo): write your description
            dx2: (todo): write your description
            dy2: (todo): write your description
            dx3: (todo): write your description
            dy3: (todo): write your description
        """
        cr = self.cr
        from_x, from_y = cr.get_current_point()
        self.curve_to(
            from_x + dx1,
            from_y + dy1,
            from_x + dx2,
            from_y + dy2,
            from_x + dx3,
            from_y + dy3,
        )

    def rectangle(self, x, y, width, height):
        """
        Draws a rectangle on the screen.

        Args:
            self: (todo): write your description
            x: (todo): write your description
            y: (todo): write your description
            width: (int): write your description
            height: (todo): write your description
        """
        x1 = x + width
        y1 = y + height
        self.move_to(x, y)
        self.line_to(x1, y)
        self.line_to(x1, y1)
        self.line_to(x, y1)
        if self.sloppiness > 0.1:
            self.line_to(x, y)
        else:
            self.close_path()


class FreeHandPainter:
    def __init__(self, subpainter: ItemPainterType, sloppiness=1.0):
        """
        Initializes the subpainter.

        Args:
            self: (todo): write your description
            subpainter: (todo): write your description
            sloppiness: (todo): write your description
        """
        self.subpainter = subpainter
        self.sloppiness = sloppiness

    def paint_item(self, item: Item, cairo):
        """
        Paints the given item.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            cairo: (todo): write your description
        """
        # Bounding  painter requires painting per item
        self.subpainter.paint_item(item, cairo)

    def paint(self, items: Sequence[Item], cairo):
        """
        Paint the given item.

        Args:
            self: (todo): write your description
            items: (todo): write your description
            cairo: (todo): write your description
        """
        self.subpainter.paint(
            items, FreeHandCairoContext(cairo, self.sloppiness),
        )
