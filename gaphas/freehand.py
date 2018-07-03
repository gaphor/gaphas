"""
Cairo context using Steve Hanov's freehand drawing code.

    # Crazyline. By Steve Hanov, 2008 Released to the public domain.

    # The idea is to draw a curve, setting two control points at
    # random close to each side of the line. The longer the line, the
    # sloppier it's drawn.

See: http://stevehanov.ca/blog/index.php?id=33 and
     http://stevehanov.ca/blog/index.php?id=93
"""
from __future__ import absolute_import

from builtins import object
from math import sqrt
from random import Random
from .painter import Context


class FreeHandCairoContext(object):

    KAPPA = 0.5522847498

    def __init__(self, cr, sloppiness=0.5):
        """
        Create context with given sloppiness. Range [0..2.0] gives acceptable
        results.

        * Draftsman: 0.0
        * Artist: 0.25
        * Cartoonist: 0.5
        * Child: 1.0
        * Drunk: 2.0
        """
        self.cr = cr
        self.sloppiness = sloppiness  # In range 0.0 .. 2.0

    def __getattr__(self, key):
        return getattr(self.cr, key)

    def line_to(self, x, y):
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
        cr = self.cr
        from_x, from_y = cr.get_current_point()
        self.line_to(from_x + dx, from_y + dy)

    def curve_to(self, x1, y1, x2, y2, x3, y3):
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

    def corner_to(self, cx, cy, x, y):
        cr = self.cr
        from_x, from_y = cr.get_current_point()

        # calculate radius of the circle.
        radius1 = Math.sqrt(
            (cx - from_x) * (cx - from_x) + (cy - from_y) * (cy - from_y)
        )

        radius2 = Math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y))

        dev_x, dev_y = cr.user_to_device(x, y)
        rand = Random((cx, cy, dev_x, dev_y, radius1, radius2)).random

        # place first control point
        c1_x = from_x + self.KAPPA * (cx - from_x) + rand() * sloppiness * radius1 / 2
        c1_y = from_y + self.KAPPA * (cy - from_y) + rand() * sloppiness * radius1 / 2

        # place second control point
        c2_x = x + self.KAPPA * (cx - x) + rand() * sloppiness * radius2 / 1.5
        c2_y = y + self.KAPPA * (cy - y) + rand() * sloppiness * radius2 / 1.5

        cr.curve_to(c1_x, c1_y, c2_x, c2_y, x3, y3)

    def rectangle(self, x, y, width, height):
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


class FreeHandPainter(object):
    def __init__(self, subpainter, sloppiness=1.0, view=None):
        self.subpainter = subpainter
        self.view = view
        self.sloppiness = sloppiness

    def set_view(self, view):
        self.view = view
        self.subpainter.set_view(view)

    def paint(self, context):
        subcontext = Context(
            cairo=FreeHandCairoContext(context.cairo, self.sloppiness),
            items=context.items,
            area=context.area,
        )
        self.subpainter.paint(subcontext)


# vi:sw=4:et:ai
