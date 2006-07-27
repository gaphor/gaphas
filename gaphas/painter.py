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
TOLERANCE = 0.5

class Painter(object):
    """Painter interface.
    """

    def paint(self, context):
        """Do the paint action (called from the View).
        """
        pass


class PainterChain(Painter):
    """Chain up a set of painters.
    like ToolChain.
    """

    def __init__(self):
        self._painters = []

    def append(self, painter):
        """Add a painter to the list of painters.
        """
        self._painters.append(painter)

    def prepend(self, painter):
        """Add a painter to the beginning of the list of painters.
        """
        self._painters.insert(0, painter)

    def paint(self, context):
        """See Painter.paint().
        """
        for painter in self._painters:
            painter.paint(context)


class DrawContext(Context):
    """Special context for draw()'ing the item. The draw-context contains
    stuff like the view, the cairo context and properties like selected and
    focused.
    """

    painter = None
    cairo = None

    def __init__(self, **kwargs):
        super(DrawContext, self).__init__(**kwargs)

    def draw_children(self):
        """Extra helper method for drawing child items from within
        the Item.draw() method.
        """
        self.painter._draw_items(self.children,
                                 self.view,
                                 self.cairo)


class ItemPainter(Painter):

    def _draw_item(self, item, view, cairo):
        cairo.save()
        try:
            cairo.set_matrix(view.matrix)
            cairo.transform(view.canvas.get_matrix_i2w(item))

            item.draw(DrawContext(painter=self,
                                  view=view,
                                  cairo=cairo,
                                  parent=view.canvas.get_parent(item),
                                  children=view.canvas.get_children(item),
                                  selected=(item in view.selected_items),
                                  focused=(item is view.focused_item),
                                  hovered=(item is view.hovered_item)))

            if DEBUG_DRAW_BOUNDING_BOX:
                try:
                    b = view.get_item_bounding_box(item)
                except KeyError:
                    pass # No bounding box right now..
                else:
                    cairo.save()
                    cairo.identity_matrix()
                    cairo.set_source_rgb(.8, 0, 0)
                    cairo.set_line_width(1.0)
                    cairo.rectangle(b[0], b[1], b[2] - b[0], b[3] - b[1])
                    cairo.stroke()
                    cairo.restore()
        finally:
            cairo.restore()

    def _draw_items(self, items, view, cairo):
        """Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            self._draw_item(item, view, cairo)

    def paint(self, context):
        cairo = context.cairo
        view = context.view
        items = view.canvas.get_root_items()
        cairo.set_tolerance(TOLERANCE)
        cairo.set_line_join(LINE_JOIN_ROUND)
        self._draw_items(items, view, cairo)


class BoundingBoxPainter(ItemPainter):
    """This specific case of an ItemPainter is used to calculate the bounding
    boxes for the items.
    """

    def _draw_items(self, items, view, cairo):
        """Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            context = view.wrap_cairo_context(cairo)
            self._draw_item(item, view, context)
            view.set_item_bounding_box(item, context.get_bounds())

    def paint(self, context):
        cairo = context.cairo
        view = context.view
        #items = context.items
        items = view.canvas.get_root_items()
        self._draw_items(items, view, cairo)


class HandlePainter(Painter):
    """Draw handles of items that are marked as selected in the view.
    """

    def _draw_handles(self, item, view, cairo, opacity=None):
        """Draw handles for an item.
        The handles are drawn in non-antialiased mode for clearity.
        """
        cairo.save()
        cairo.identity_matrix()
        #cairo.set_matrix(self._matrix)
        m = Matrix(*view.canvas.get_matrix_i2w(item))
        m *= view._matrix
        if not opacity:
            opacity = (item is view.focused_item) and .7 or .4
        for h in item.handles():
            if h.connected_to:
                r, g, b = 1, 0, 0
            elif h.movable:
                r, g, b = 0, 1, 0
            else:
                r, g, b = 0, 0, 1

            cairo.save()
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
            cairo.set_line_width(1)
            cairo.stroke()
            cairo.restore()
        cairo.restore()

    def paint(self, context):
        view = context.view
        cairo = context.cairo
        items = view.canvas.get_all_items()
        # Draw handles of selected items on top of the items.
        # Conpare with canvas.get_all_items() to determine drawing order.
        for item in (i for i in items if i in view.selected_items):
            self._draw_handles(item, view, cairo)
        item = view.hovered_item
        if item and item not in view.selected_items:
            self._draw_handles(item, view, cairo, opacity=.25)


class ToolPainter(Painter):
    """ToolPainter allows the Tool defined on a view to do some special
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
    """Default painter, containing item, handle and tool painters.
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
