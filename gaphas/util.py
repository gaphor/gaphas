"""
Helper funtions and classes for Cairo (drawing engine used by the canvas).
"""

from math import pi


def text_extents(cr, text):
    """Simple way to determine the size of a piece of text.
    """
    x_bearing, y_bearing, width, height, x_adv, y_adv = c.text_extents(text)
    return width + x_bearing, height + y_bearing


def text_center(cr, x, y, text):
    """Draw text using (x, y) as center.
    x    - center x
    y    - center y
    text - text to print (utf8)
    """
    x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(text)
    x = 0.5 - (w / 2 + x_bear) + x
    y = 0.5 - (h / 2 + y_bear) + y
    cr.move_to(x, y)
    cr.show_text(text)


def path_ellipse (cr, x, y, width, height, angle=0):
    """Draw an ellipse.
    x      - center x
    y      - center y
    width  - width of ellipse  (in x direction when angle=0)
    height - height of ellipse (in y direction when angle=0)
    angle  - angle in radians to rotate, clockwise
    """
    cr.save()
    cr.translate (x, y)
    cr.rotate (angle)
    cr.scale (width / 2.0, height / 2.0)
    cr.arc (0.0, 0.0, 1.0, 0.0, 2.0 * pi)
    cr.restore()


# vim:sw=4:et
