"""
The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes care of a layer in the canvas (such as grid, items
and handles).
"""
from __future__ import division

from builtins import object

__version__ = "$Revision$"
# $HeadURL$

from cairo import Matrix, ANTIALIAS_NONE, LINE_JOIN_ROUND

from gaphas.canvas import Context
from gaphas.geometry import Rectangle
from gaphas.item import Line
from gaphas.aspect import PaintFocused


DEBUG_DRAW_BOUNDING_BOX = False

# The tolerance for Cairo. Bigger values increase speed and reduce accuracy
# (default: 0.1)
TOLERANCE = 0.8


class Painter(object):
    """
    Painter interface.
    """

    def __init__(self, view=None):
        self.view = view

    def set_view(self, view):
        self.view = view

    def paint(self, context):
        """
        Do the paint action (called from the View).
        """
        pass


class PainterChain(Painter):
    """
    Chain up a set of painters.
    like ToolChain.
    """

    def __init__(self, view=None):
        super(PainterChain, self).__init__(view)
        self._painters = []

    def set_view(self, view):
        self.view = view
        for painter in self._painters:
            painter.set_view(self.view)

    def append(self, painter):
        """
        Add a painter to the list of painters.
        """
        self._painters.append(painter)
        painter.set_view(self.view)
        return self

    def prepend(self, painter):
        """
        Add a painter to the beginning of the list of painters.
        """
        self._painters.insert(0, painter)

    def paint(self, context):
        """
        See Painter.paint().
        """
        for painter in self._painters:
            painter.paint(context)


class DrawContext(Context):
    """
    Special context for draw()'ing the item. The draw-context contains
    stuff like the cairo context and properties like selected and
    focused.
    """

    deprecated = False

    def __init__(self, **kwargs):
        super(DrawContext, self).__init__(**kwargs)


class ItemPainter(Painter):

    draw_all = False

    def _draw_item(self, item, cairo, area=None):
        view = self.view
        cairo.save()
        try:
            cairo.set_matrix(view.matrix)
            cairo.transform(view.canvas.get_matrix_i2c(item))

            item.draw(
                DrawContext(
                    painter=self,
                    cairo=cairo,
                    _area=area,
                    _item=item,
                    selected=(item in view.selected_items),
                    focused=(item is view.focused_item),
                    hovered=(item is view.hovered_item),
                    dropzone=(item is view.dropzone_item),
                    draw_all=self.draw_all,
                )
            )

        finally:
            cairo.restore()

    def _draw_items(self, items, cairo, area=None):
        """
        Draw the items.
        """
        for item in items:
            self._draw_item(item, cairo, area=area)
            if DEBUG_DRAW_BOUNDING_BOX:
                self._draw_bounds(item, cairo)

    def _draw_bounds(self, item, cairo):
        view = self.view
        try:
            b = view.get_item_bounding_box(item)
        except KeyError:
            pass  # No bounding box right now..
        else:
            cairo.save()
            cairo.identity_matrix()
            cairo.set_source_rgb(0.8, 0, 0)
            cairo.set_line_width(1.0)
            cairo.rectangle(*b)
            cairo.stroke()
            cairo.restore()

    def paint(self, context):
        cairo = context.cairo
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)
        self._draw_items(context.items, cairo, context.area)


class CairoBoundingBoxContext(object):
    """
    Delegate all calls to the wrapped CairoBoundingBoxContext,
    intercept ``stroke()``, ``fill()`` and a few others so the
    bounding box of the item involved can be calculated.
    """

    def __init__(self, cairo):
        self._cairo = cairo
        self._bounds = None  # a Rectangle object

    def __getattr__(self, key):
        return getattr(self._cairo, key)

    def get_bounds(self):
        """
        Return the bounding box.
        """
        return self._bounds or Rectangle()

    def _update_bounds(self, bounds):
        if bounds:
            if not self._bounds:
                self._bounds = bounds
            else:
                self._bounds += bounds

    def _extents(self, extents_func, line_width=False):
        """
        Calculate the bounding box for a given drawing operation.  if
        ``line_width`` is True, the current line-width is taken into
        account.
        """
        cr = self._cairo
        cr.save()
        cr.identity_matrix()
        x0, y0, x1, y1 = extents_func()
        b = Rectangle(x0, y0, x1=x1, y1=y1)
        cr.restore()
        if b and line_width:
            # Do this after the restore(), so we can get the proper width.
            lw = cr.get_line_width() / 2
            d = cr.user_to_device_distance(lw, lw)
            b.expand(d[0] + d[1])
        self._update_bounds(b)
        return b

    def fill(self, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cairo
        if not b:
            b = self._extents(cr.fill_extents)
        cr.fill()

    def fill_preserve(self, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cairo
        if not b:
            b = self._extents(cr.fill_extents)

    def stroke(self, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cairo
        if not b:
            b = self._extents(cr.stroke_extents, line_width=True)
        cr.stroke()

    def stroke_preserve(self, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cairo
        if not b:
            b = self._extents(cr.stroke_extents, line_width=True)

    def show_text(self, utf8, b=None):
        """
        Interceptor for Cairo drawing method.
        """
        cr = self._cairo
        if not b:
            x, y = cr.get_current_point()
            e = cr.text_extents(utf8)
            x0, y0 = cr.user_to_device(x + e[0], y + e[1])
            x1, y1 = cr.user_to_device(x + e[0] + e[2], y + e[1] + e[3])
            b = Rectangle(x0, y0, x1=x1, y1=y1)
            self._update_bounds(b)
        cr.show_text(utf8)


class BoundingBoxPainter(ItemPainter):
    """
    This specific case of an ItemPainter is used to calculate the
    bounding boxes (in canvas coordinates) for the items.
    """

    draw_all = True

    def _draw_item(self, item, cairo, area=None):
        cairo = CairoBoundingBoxContext(cairo)
        super(BoundingBoxPainter, self)._draw_item(item, cairo)
        bounds = cairo.get_bounds()

        # Update bounding box with handles.
        view = self.view
        i2v = view.get_matrix_i2v(item).transform_point
        for h in item.handles():
            cx, cy = i2v(*h.pos)
            bounds += (cx - 5, cy - 5, 9, 9)

        bounds.expand(1)
        view.set_item_bounding_box(item, bounds)

    def _draw_items(self, items, cairo, area=None):
        """
        Draw the items.
        """
        for item in items:
            self._draw_item(item, cairo)

    def paint(self, context):
        self._draw_items(context.items, context.cairo)


class HandlePainter(Painter):
    """
    Draw handles of items that are marked as selected in the view.
    """

    def _draw_handles(self, item, cairo, opacity=None, inner=False):
        """
        Draw handles for an item.
        The handles are drawn in non-antialiased mode for clarity.
        """
        view = self.view
        cairo.save()
        i2v = view.get_matrix_i2v(item)
        if not opacity:
            opacity = (item is view.focused_item) and 0.7 or 0.4

        cairo.set_line_width(1)

        get_connection = view.canvas.get_connection
        for h in item.handles():
            if not h.visible:
                continue
            # connected and not being moved, see HandleTool.on_button_press
            if get_connection(h):
                r, g, b = 1, 0, 0
            # connected but being moved, see HandleTool.on_button_press
            elif get_connection(h):
                r, g, b = 1, 0.6, 0
            elif h.movable:
                r, g, b = 0, 1, 0
            else:
                r, g, b = 0, 0, 1

            cairo.identity_matrix()
            cairo.set_antialias(ANTIALIAS_NONE)
            cairo.translate(*i2v.transform_point(*h.pos))
            cairo.rectangle(-4, -4, 8, 8)
            if inner:
                cairo.rectangle(-3, -3, 6, 6)
            cairo.set_source_rgba(r, g, b, opacity)
            cairo.fill_preserve()
            if h.connectable:
                cairo.move_to(-2, -2)
                cairo.line_to(2, 3)
                cairo.move_to(2, -2)
                cairo.line_to(-2, 3)
            cairo.set_source_rgba(r / 4.0, g / 4.0, b / 4.0, opacity * 1.3)
            cairo.stroke()
        cairo.restore()

    def paint(self, context):
        view = self.view
        canvas = view.canvas
        cairo = context.cairo
        # Order matters here:
        for item in canvas.sort(view.selected_items):
            self._draw_handles(item, cairo)
        # Draw nice opaque handles when hovering an item:
        item = view.hovered_item
        if item and item not in view.selected_items:
            self._draw_handles(item, cairo, opacity=0.25)
        item = view.dropzone_item
        if item and item not in view.selected_items:
            self._draw_handles(item, cairo, opacity=0.25, inner=True)


class ToolPainter(Painter):
    """
    ToolPainter allows the Tool defined on a view to do some special
    drawing.
    """

    def paint(self, context):
        view = self.view
        cairo = context.cairo
        if view.tool:
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(context)
            cairo.restore()


class FocusedItemPainter(Painter):
    """
    This painter allows for drawing on top off all other layers for
    the focused item.
    """

    def paint(self, context):
        view = self.view
        item = view.hovered_item
        if item and item is view.focused_item:
            PaintFocused(item, view).paint(context)


def DefaultPainter(view=None):
    """
    Default painter, containing item, handle and tool painters.
    """
    return (
        PainterChain(view)
        .append(ItemPainter())
        .append(HandlePainter())
        .append(FocusedItemPainter())
        .append(ToolPainter())
    )


# vim: sw=4:et:ai
