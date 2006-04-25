"""
The painter module provides different painters for parts of the canvas.

Painters can be swapped in and out.

Each painter takes are of a layer in the canvas (such as grid, items
and handles).
"""

from cairo import Matrix, ANTIALIAS_NONE

from canvas import Context
from geometry import Rectangle

DEBUG_DRAW_BOUNDING_BOX = False

class Painter(object):
    """Painter interface.
    """

    def paint(self, context):
        pass


class PainterChain(Painter):
    """Chain up a set of painters.
    like ToolChain.
    """

    def __init__(self):
        self._painters = []

    def append(self, painter):
        self._painters.append(painter)

    def prepend(self, painter):
        self._painters.insert(0, painter)

    def paint(self, context):
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
                                 self.cairo,
                                 self.update_bounds)

class CairoContextWrapper(object):
    """Delegate all calls to the wrapped CairoContext, intercept
    stroke(), fill() and a few others so the bounding box of the
    item involved can be calculated.
    """

    def __init__(self, cairo):
        self._cairo = cairo
        self._bounds = None # a Rectangle object

    def __getattr__(self, key):
        return getattr(self._cairo, key)

    def _update_bounds(self, bounds):
        if not self._bounds:
            self._bounds = Rectangle(*bounds)
        else:
            self._bounds += bounds

    def _extents(self, funcname):
        ctx = self._cairo
        ctx.save()
        ctx.identity_matrix()
        self._update_bounds(getattr(ctx, funcname)())
        ctx.restore()
        
    def fill(self):
        self._extents('fill_extents')
        return self._cairo.fill()

    def fill_preserve(self):
        self._extents('fill_extents')
        return self._cairo.fill_preserve()

    def stroke(self):
        self._extents('stroke_extents')
        return self._cairo.stroke()

    def stroke_preserve(self):
        self._extents('stroke_extents')
        return self._cairo.stroke_preserve()

    def show_text(self, utf8):
        cairo = self._cairo
        e = cairo.text_extents(utf8)
        x0, y0 = cairo.user_to_device(e[0], e[1])
        x1, y1 = cairo.user_to_device(e[0]+e[2], e[1]+e[3])
        self._update_bounds((x0, y0, x1, y1))
        return cairo.show_text(utf8)


class ItemPainter(Painter):

    def _draw_items(self, items, view, cairo, update_bounds):
        """Draw the items. This method can also be called from DrawContext
        to draw sub-items.
        """
        for item in items:
            cairo.save()
            try:
                cairo.set_matrix(view.matrix)
                cairo.transform(view.canvas.get_matrix_i2w(item))

                if update_bounds:
                    the_context = CairoContextWrapper(cairo)
                else:
                    # No wrapper:
                    the_context = cairo

                item.draw(DrawContext(painter=self,
                                      update_bounds=update_bounds,
                                      view=view,
                                      cairo=the_context,
                                      parent=view.canvas.get_parent(item),
                                      children=view.canvas.get_children(item),
                                      selected=(item in view.selected_items),
                                      focused=(item is view.focused_item),
                                      hovered=(item is view.hovered_item)))

                if update_bounds:
                    view.set_item_bounding_box(item, the_context._bounds)

                if DEBUG_DRAW_BOUNDING_BOX:
                    b = view.get_item_bounding_box(item)
                    cairo.save()
                    cairo.identity_matrix()
                    cairo.set_source_rgb(.8, 0, 0)
                    cairo.set_line_width(1.0)
                    cairo.rectangle(b[0], b[1], b[2] - b[0], b[3] - b[1])
                    cairo.stroke()
                    cairo.restore()
            finally:
                cairo.restore()

    def paint(self, context):
        cairo = context.cairo
        view = context.view
        items = view.canvas.get_root_items()
        update_bounds = context.update_bounds
        self._draw_items(items, view, cairo, update_bounds)


class HandlePainter(Painter):
    """Draw handles of items that are marked as selected in the view.
    """

    def _draw_handles(self, item, view, cairo):
        """Draw handles for an item.
        The handles are drawn in non-antialiased mode for clearity.
        """
        cairo.save()
        cairo.identity_matrix()
        #cairo.set_matrix(self._matrix)
        m = Matrix(*view.canvas.get_matrix_i2w(item))
        m *= view._matrix
        opacity = (item is view.focused_item) and .7 or .4
        for h in item.handles():
            cairo.save()
            cairo.set_antialias(ANTIALIAS_NONE)
            cairo.translate(*m.transform_point(h.x, h.y))
            cairo.rectangle(-4, -4, 8, 8)
            cairo.set_source_rgba(0, 1, 0, opacity)
            cairo.fill_preserve()
            cairo.move_to(-2, -2)
            cairo.line_to(2, 3)
            cairo.move_to(2, -2)
            cairo.line_to(-2, 3)
            cairo.set_source_rgba(0, .2, 0, 0.9)
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
