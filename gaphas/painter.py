"""
The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes are of a layer in the canvas (such as grid, items
and handles).
"""

__version__ = "$Revision$"
# $HeadURL$

from cairo import Matrix, ANTIALIAS_NONE, LINE_JOIN_ROUND

from canvas import Context
from geometry import Rectangle

DEBUG_DRAW_BOUNDING_BOX = False

# The tolerance for Cairo. Bigger values increase speed and reduce accuracy
# (default: 0.1)
TOLERANCE = 0.8

class Painter(object):
    """
    Painter interface.
    """

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

    def __init__(self):
        self._painters = []

    def append(self, painter):
        """
        Add a painter to the list of painters.
        """
        self._painters.append(painter)

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
    stuff like the view, the cairo context and properties like selected and
    focused.
    """

    painter = None
    cairo = None

    def __init__(self, **kwargs):
        super(DrawContext, self).__init__(**kwargs)

    def draw_children(self):
        """
        Extra helper method for drawing child items from within
        the Item.draw() method.
        """
        self.painter._draw_items(self.children,
                                 self.view,
                                 self.cairo,
                                 self._area)


class ItemPainter(Painter):

    draw_all = False

    def _draw_item(self, item, view, cairo, area=None):
        cairo.save()
        try:
            cairo.set_matrix(view.matrix)
            cairo.transform(view.canvas.get_matrix_i2w(item))

            item.draw(DrawContext(painter=self,
                                  view=view,
                                  cairo=cairo,
                                  _area=area,
                                  parent=view.canvas.get_parent(item),
                                  children=view.canvas.get_children(item),
                                  selected=(item in view.selected_items),
                                  focused=(item is view.focused_item),
                                  hovered=(item is view.hovered_item),
                                  dropzone=(item is view.dropzone_item),
                                  draw_all=self.draw_all))

        finally:
            cairo.restore()

    def _draw_items(self, items, view, cairo, area=None):
        """
        Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            if not area or view.get_item_bounding_box(item) - area:
                self._draw_item(item, view, cairo, area=area)
                if DEBUG_DRAW_BOUNDING_BOX:
                    self._draw_bounds(item, view, cairo)

    def _draw_bounds(self, item, view, cairo):
        try:
            b = view.get_item_bounding_box(item)
        except KeyError:
            pass # No bounding box right now..
        else:
            cairo.save()
            cairo.identity_matrix()
            cairo.set_source_rgb(.8, 0, 0)
            cairo.set_line_width(1.0)
            cairo.rectangle(*b)
            cairo.stroke()
            cairo.restore()

    def paint(self, context):
        cairo = context.cairo
        view = context.view
        area = context.area
        items = view.canvas.get_root_items()
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)
        self._draw_items(items, view, cairo, area)


class CairoBoundingBoxContext(object):
    """
    Delegate all calls to the wrapped CairoBoundingBoxContext, intercept
    stroke(), fill() and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cairo):
        self._cairo = cairo
        self._nested = isinstance(cairo, CairoBoundingBoxContext)
        self._bounds = None # a Rectangle object

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
        Calculate the bounding box for a given drawing operation.
        if @line_width is True, the current line-width is taken into account.
        """
        cr = self._cairo
        cr.save()
        cr.identity_matrix()
        x0, y0, x1, y1 = extents_func()
        b = Rectangle(x0, y0, x1=x1, y1=y1)
        cr.restore()
        if b and line_width:
            # Do this after the restore(), so we can get the proper width.
            lw = cr.get_line_width()/2
            d = cr.user_to_device_distance(lw, lw)
            b.expand(d[0]+d[1])
        self._update_bounds(b)
        return b

    def fill(self, b=None):
        cr = self._cairo
        if not b:
            b = self._extents(cr.fill_extents)
        if self._nested:
            cr.fill(b)
        else:
            cr.fill()


    def fill_preserve(self, b=None):
        cr = self._cairo
        if not b:
            b = self._extents(cr.fill_extents)
        if self._nested:
            cr.fill_preserve(b)

    def stroke(self, b=None):
        cr = self._cairo
        if not b:
            b = self._extents(cr.stroke_extents, line_width=True)
        if self._nested:
            cr.stroke(b)
        else:
            cr.stroke()

    def stroke_preserve(self, b=None):
        cr = self._cairo
        if not b:
            b = self._extents(cr.stroke_extents, line_width=True)
        if self._nested:
            cr.stroke_preserve(b)

    def show_text(self, utf8, b=None):
        cr = self._cairo
        if not b:
            x, y = cr.get_current_point()
            e = cr.text_extents(utf8)
            x0, y0 = cr.user_to_device(x+e[0], y+e[1])
            x1, y1 = cr.user_to_device(x+e[0]+e[2], y+e[1]+e[3])
            b = Rectangle(x0, y0, x1=x1, y1=y1)
            self._update_bounds(b)
        if self._nested:
            cr.show_text(utf8, b)
        else:
            cr.show_text(utf8)

class BoundingBoxPainter(ItemPainter):
    """
    This specific case of an ItemPainter is used to calculate the bounding
    boxes (in canvas coordinates) for the items.
    """

    draw_all = True

    def _draw_handles(self, item, view, cairo):
        """
        Update the bounding box with handle's position.
        """
        cairo.save()
        try:
            m = Matrix(*view.canvas.get_matrix_i2w(item))
            m *= view._matrix

            for h in item.handles():
                cairo.identity_matrix()
                cairo.translate(*m.transform_point(h.x, h.y))
                cairo.rectangle(-5, -5, 9, 9)
                cairo.fill()
        finally:
            cairo.restore()

    def _draw_item(self, item, view, cairo, area=None):
        cairo = CairoBoundingBoxContext(cairo)
        super(BoundingBoxPainter, self)._draw_item(item, view, cairo)
        self._draw_handles(item, view, cairo)
        view.set_item_bounding_box(item, cairo.get_bounds())

    def _draw_items(self, items, view, cairo, area=None):
        """
        Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            self._draw_item(item, view, cairo)

    def paint(self, context):
        cairo = context.cairo
        view = context.view
        items = context.items
        self._draw_items(items, view, cairo)


class HandlePainter(Painter):
    """
    Draw handles of items that are marked as selected in the view.
    """

    def _draw_handles(self, item, view, cairo, opacity=None):
        """
        Draw handles for an item.
        The handles are drawn in non-antialiased mode for clearity.
        """
        cairo.save()
        m = Matrix(*view.canvas.get_matrix_i2w(item))
        m *= view._matrix
        if not opacity:
            opacity = (item is view.focused_item) and .7 or .4

        cairo.set_line_width(1)

        for h in item.handles():
            if not h.visible:
                continue
            if h.connected_to:
                r, g, b = 1, 0, 0
            elif h.movable:
                r, g, b = 0, 1, 0
            else:
                r, g, b = 0, 0, 1

            cairo.identity_matrix()
            cairo.set_antialias(ANTIALIAS_NONE)
            cairo.translate(*m.transform_point(h.x, h.y))
            cairo.rectangle(-4, -4, 8, 8)
            cairo.set_source_rgba(r, g, b, opacity)
            cairo.fill_preserve()
            if h.connectable:
                cairo.move_to(-2, -2)
                cairo.line_to(2, 3)
                cairo.move_to(2, -2)
                cairo.line_to(-2, 3)
            cairo.set_source_rgba(r/4., g/4., b/4., opacity*1.3)
            cairo.stroke()
        cairo.restore()

    def paint(self, context):
        view = context.view
        cairo = context.cairo
        items = view.canvas.get_all_items()
        # Draw handles of selected items on top of the items.
        # Compare with canvas.get_all_items() to determine drawing order.
        for item in (i for i in items if i in view.selected_items):
            self._draw_handles(item, view, cairo)
        item = view.hovered_item
        if item and item not in view.selected_items:
            self._draw_handles(item, view, cairo, opacity=.25)


class ToolPainter(Painter):
    """
    ToolPainter allows the Tool defined on a view to do some special
    drawing.
    """

    def paint(self, context):
        view = context.view
        cairo = context.cairo
        if view.tool:
            cairo.save()
            cairo.identity_matrix()
            view.tool.draw(Context(view=view, cairo=cairo))
            cairo.restore()


def DefaultPainter():
    """
    Default painter, containing item, handle and tool painters.
    """
    chain = PainterChain()
    chain.append(ItemPainter())
    chain.append(HandlePainter())
    chain.append(ToolPainter())
    return chain


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:
