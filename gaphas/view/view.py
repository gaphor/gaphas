from typing import Optional, Tuple

from gaphas.canvas import Canvas, Context
from gaphas.geometry import Rectangle
from gaphas.item import Item
from gaphas.matrix import Matrix
from gaphas.painter import BoundingBoxPainter, DefaultPainter, ItemPainter
from gaphas.quadtree import Quadtree


class View:
    """View class for gaphas.Canvas objects."""

    def __init__(self, canvas=None):
        self._matrix = Matrix()
        self._painter = DefaultPainter(self)
        self._bounding_box_painter = BoundingBoxPainter(ItemPainter(self), self)

        self._qtree: Quadtree[Item, Tuple[float, float, float, float]] = Quadtree()

        self._canvas: Optional[Canvas] = None
        if canvas:
            self._set_canvas(canvas)

    @property
    def matrix(self) -> Matrix:
        """Canvas to view transformation matrix."""
        return self._matrix

    def _set_canvas(self, canvas):
        """
        Use view.canvas = my_canvas to set the canvas to be rendered
        in the view.
        """
        if self._canvas:
            self._qtree.clear()

        self._canvas = canvas

    canvas = property(lambda s: s._canvas, _set_canvas)

    def _set_painter(self, painter):
        """Set the painter to use.

        Painters should implement painter.Painter.
        """
        self._painter = painter
        painter.set_view(self)

    painter = property(lambda s: s._painter, _set_painter)

    def _set_bounding_box_painter(self, painter):
        """Set the painter to use for bounding box calculations."""
        self._bounding_box_painter = painter
        painter.set_view(self)

    bounding_box_painter = property(
        lambda s: s._bounding_box_painter, _set_bounding_box_painter
    )

    def get_port_at_point(self, vpos, distance=10, exclude=None):
        """Find item with port closest to specified position.

        List of items to be ignored can be specified with `exclude`
        parameter.

        Tuple is returned

        - found item
        - closest, connectable port
        - closest point on found port (in view coordinates)

        :Parameters:
         vpos
            Position specified in view coordinates.
         distance
            Max distance from point to a port (default 10)
         exclude
            Set of items to ignore.
        """
        v2i = self.get_matrix_v2i
        vx, vy = vpos

        max_dist = distance
        port = None
        glue_pos = None
        item = None

        rect = (vx - distance, vy - distance, distance * 2, distance * 2)
        items = reversed(self.get_items_in_rectangle(rect))
        for i in items:
            if i in exclude:
                continue
            for p in i.ports():
                if not p.connectable:
                    continue

                ix, iy = v2i(i).transform_point(vx, vy)
                pg, d = p.glue((ix, iy))

                if d >= max_dist:
                    continue

                max_dist = d
                item = i
                port = p

                # transform coordinates from connectable item space to view
                # space
                i2v = self.get_matrix_i2v(i).transform_point
                glue_pos = i2v(*pg)

        return item, port, glue_pos

    def get_items_in_rectangle(self, rect, intersect=True):
        """Return the items in the rectangle 'rect'.

        Items are automatically sorted in canvas' processing order.
        """
        assert self._canvas
        if intersect:
            items = self._qtree.find_intersect(rect)
        else:
            items = self._qtree.find_inside(rect)
        return self._canvas.sort(items)

    def set_item_bounding_box(self, item, bounds):
        """Update the bounding box of the item.

        ``bounds`` is in view coordinates.

        Coordinates are calculated back to item coordinates, so
        matrix-only updates can occur.
        """
        v2i = self.get_matrix_v2i(item).transform_point
        ix0, iy0 = v2i(bounds.x, bounds.y)
        ix1, iy1 = v2i(bounds.x1, bounds.y1)
        self._qtree.add(item=item, bounds=bounds, data=(ix0, iy0, ix1, iy1))

    def get_item_bounding_box(self, item):
        """Get the bounding box for the item, in view coordinates."""
        return self._qtree.get_bounds(item)

    bounding_box = property(lambda s: Rectangle(*s._qtree.soft_bounds))

    def update_bounding_box(self, cr, items=None):
        """Update the bounding boxes of the canvas items for this view, in
        canvas coordinates."""
        painter = self._bounding_box_painter
        if items is None:
            items = self.canvas.get_all_items()

        # The painter calls set_item_bounding_box() for each rendered item.
        painter.paint(Context(cairo=cr, items=items))

    def get_matrix_i2v(self, item):
        """Get Item to View matrix for ``item``."""
        return item.matrix_i2c.multiply(self._matrix)

    def get_matrix_v2i(self, item):
        """Get View to Item matrix for ``item``."""
        m = self.get_matrix_i2v(item)
        m.invert()
        return m
