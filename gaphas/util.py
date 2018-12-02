"""
Helper functions and classes for Cairo (drawing engine used by the
canvas).
"""
from __future__ import division

from math import pi

import cairo


def text_extents(cr, text, font=None, multiline=False, padding=1):
    """
    Simple way to determine the size of a piece of text.
    """
    if not text:
        return 0, 0
    if font:
        cr.save()
        text_set_font(cr, font)

    if multiline:
        width, height = 0, 0
        for line in text.split("\n"):
            x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(line)
            width = max(width, w)
            height += h + padding
    else:
        x_bear, y_bear, width, height, x_adv, y_adv = cr.text_extents(text)
        # width, height = width + x_bearing, height + y_bearing

    if font:
        cr.restore()
    return width, height


def text_center(cr, x, y, text):
    text_align(cr, x, y, text, align_x=0, align_y=0)


def text_align(cr, x, y, text, align_x=0, align_y=0, padding_x=0, padding_y=0):
    """
    Draw text relative to (x, y).
    x, y - coordinates
    text - text to print (utf8)
    align_x - -1 (top), 0 (middle), 1 (bottom)
    align_y - -1 (left), 0 (center), 1 (right)
    padding_x - padding (extra offset), always > 0
    padding_y - padding (extra offset), always > 0
    """
    if not text:
        return

    x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(text)
    if align_x == 0:
        x = 0.5 - (w / 2 + x_bear) + x
    elif align_x < 0:
        x = -(w + x_bear) + x - padding_x
    else:
        x = x + padding_x
    if align_y == 0:
        y = 0.5 - (h / 2 + y_bear) + y
    elif align_y < 0:
        y = -(h + y_bear) + y - padding_y
    else:
        y = -y_bear + y + padding_y
    cr.move_to(x, y)
    cr.show_text(text)


def text_multiline(cr, x, y, text, padding=1):
    """
    Draw a string of text with embedded newlines.
    cr - cairo context
    x - leftmost x
    y - topmost y
    text - text to draw
    padding - additional padding between lines.
    """
    if not text:
        return
    # cr.move_to(x, y)
    for line in text.split("\n"):
        x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(text)
        y += h
        cr.move_to(x, y)
        cr.show_text(line)


def text_underline(cr, x, y, text, offset=1.5):
    """
    Draw text with underline.
    """
    x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(text)
    cr.move_to(x, y - y_bear)
    cr.show_text(text)
    cr.move_to(x, y - y_bear + offset)
    cr.set_line_width(1.0)
    cr.rel_line_to(x_adv, 0)
    cr.stroke()


def text_set_font(cr, font):
    """
    Set the font from a string. E.g. 'sans 10' or 'sans italic bold
    12' only restriction is that the font name should be the first
    option and the font size as last argument
    """
    font = font.split()
    cr.select_font_face(
        font[0],
        "italic" in font and cairo.FONT_SLANT_ITALIC or cairo.FONT_SLANT_NORMAL,
        "bold" in font and cairo.FONT_WEIGHT_BOLD or cairo.FONT_WEIGHT_NORMAL,
    )
    cr.set_font_size(float(font[-1]))


def path_ellipse(cr, x, y, width, height, angle=0):
    """
    Draw an ellipse.
    x      - center x
    y      - center y
    width  - width of ellipse  (in x direction when angle=0)
    height - height of ellipse (in y direction when angle=0)
    angle  - angle in radians to rotate, clockwise
    """
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.scale(width / 2.0, height / 2.0)
    cr.move_to(1.0, 0.0)
    cr.arc(0.0, 0.0, 1.0, 0.0, 2.0 * pi)
    cr.restore()


# vim:sw=4:et
