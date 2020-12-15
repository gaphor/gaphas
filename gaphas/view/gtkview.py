"""This module contains everything to display a model on a screen."""
from __future__ import annotations

from typing import Collection, Iterable, Optional, Set, Tuple

import cairo
from gi.repository import Gdk, GLib, GObject, Gtk

from gaphas.canvas import instant_cairo_context
from gaphas.decorators import g_async
from gaphas.geometry import Rect, Rectangle
from gaphas.item import Item
from gaphas.matrix import Matrix
from gaphas.painter import BoundingBoxPainter, DefaultPainter, ItemPainter, Painter
from gaphas.quadtree import Quadtree, QuadtreeBucket
from gaphas.view.model import Model
from gaphas.view.scrolling import Scrolling
from gaphas.view.selection import Selection

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = Gdk.CursorType.LEFT_PTR


class GtkView(Gtk.DrawingArea, Gtk.Scrollable):
    """GTK+ widget for rendering a gaphas.view.model.Model to a screen.  The
    view uses Tools to handle events and Painters to draw. Both are
    configurable.

    The widget already contains adjustment objects (`hadjustment`,
    `vadjustment`) to be used for scrollbars.

    This view registers itself on the model, so it will receive
    update events.
    """

    # Just defined a name to make GTK register this class.
    __gtype_name__ = "GaphasView"

    # properties required by Gtk.Scrollable
    __gproperties__ = {
        "hscroll-policy": (
            Gtk.ScrollablePolicy,
            "hscroll-policy",
            "hscroll-policy",
            Gtk.ScrollablePolicy.MINIMUM,
            GObject.ParamFlags.READWRITE,
        ),
        "hadjustment": (
            Gtk.Adjustment,
            "hadjustment",
            "hadjustment",
            GObject.ParamFlags.READWRITE,
        ),
        "vscroll-policy": (
            Gtk.ScrollablePolicy,
            "vscroll-policy",
            "vscroll-policy",
            Gtk.ScrollablePolicy.MINIMUM,
            GObject.ParamFlags.READWRITE,
        ),
        "vadjustment": (
            Gtk.Adjustment,
            "vadjustment",
            "vadjustment",
            GObject.ParamFlags.READWRITE,
        ),
    }

    def __init__(self, model: Optional[Model] = None, selection: Selection = None):
        """Create a new view.

        Args:
            model (Model): optional model to be set on construction time.
            selection (Selection): optional selection object, in case the default
                selection object (hover/select/focus) is not enough.
        """
        Gtk.DrawingArea.__init__(self)

        self._dirty_items: Set[Item] = set()
        self._dirty_matrix_items: Set[Item] = set()

        self._back_buffer: Optional[cairo.Surface] = None
        self._back_buffer_needs_resizing = True

        self._controllers: Set[Gtk.EventController] = set()

        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
            | Gdk.EventMask.KEY_RELEASE_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.STRUCTURE_MASK
        )

        def alignment_updated(matrix: Matrix) -> None:
            assert self._model
            self._matrix *= matrix  # type: ignore[operator]

            # Force recalculation of the bounding boxes:
            self.request_update((), self._model.get_all_items())

        self._scrolling = Scrolling(alignment_updated)

        self._selection = selection or Selection()

        self._matrix = Matrix()
        self._painter: Painter = DefaultPainter(self)
        self._bounding_box_painter: Painter = BoundingBoxPainter(
            ItemPainter(self._selection)
        )

        self._qtree: Quadtree[Item, Tuple[float, float, float, float]] = Quadtree()

        self._model: Optional[Model] = None
        if model:
            self.model = model

        self._selection.add_handler(self.queue_redraw)

    def do_get_property(self, prop: str) -> object:
        return self._scrolling.get_property(prop)

    def do_set_property(self, prop: str, value: object) -> None:
        self._scrolling.set_property(prop, value)

    @property
    def matrix(self) -> Matrix:
        """Model root to view transformation matrix."""
        return self._matrix

    def get_matrix_i2v(self, item: Item) -> Matrix:
        """Get Item to View matrix for ``item``."""
        return item.matrix_i2c.multiply(self._matrix)

    def get_matrix_v2i(self, item: Item) -> Matrix:
        """Get View to Item matrix for ``item``."""
        m = self.get_matrix_i2v(item)
        m.invert()
        return m

    @property
    def model(self) -> Optional[Model]:
        """The model."""
        return self._model

    @model.setter
    def model(self, model: Optional[Model]) -> None:
        if self._model:
            self._model.unregister_view(self)
            self._selection.clear()
            self._qtree.clear()

        self._model = model

        if self._model:
            self._model.register_view(self)
            self.request_update(self._model.get_all_items())

    @property
    def painter(self) -> Painter:
        """Painter for drawing the view."""
        return self._painter

    @painter.setter
    def painter(self, painter: Painter) -> None:
        self._painter = painter

    @property
    def bounding_box_painter(self) -> Painter:
        """Special painter for calculating item bounding boxes."""
        return self._bounding_box_painter

    @bounding_box_painter.setter
    def bounding_box_painter(self, painter: Painter) -> None:
        self._bounding_box_painter = painter

    @property
    def selection(self) -> Selection:
        """Selected, focused and hovered items."""
        return self._selection

    @selection.setter
    def selection(self, selection: Selection) -> None:
        """Selected, focused and hovered items."""
        self._selection = selection
        self.queue_redraw()

    @property
    def bounding_box(self) -> Rectangle:
        """The bounding box of the complete view, relative to the view port."""
        return Rectangle(*self._qtree.soft_bounds)

    @property
    def hadjustment(self) -> Gtk.Adjustment:
        """Gtk adjustment object for use with a scrollbar."""
        return self._scrolling.hadjustment

    @property
    def vadjustment(self) -> Gtk.Adjustment:
        """Gtk adjustment object for use with a scrollbar."""
        return self._scrolling.vadjustment

    def add_controller(self, *controllers: Gtk.EventController) -> None:
        """Add a controller.

        A convenience method, so you have a place to store the event
        controllers. Events controllers are linked to a widget (in GTK3)
        on creation time, so calling this method is not necessary.
        """
        self._controllers.update(controllers)

    def remove_controller(self, controller: Gtk.EventController) -> bool:
        """Remove a controller.

        The event controller's propagation phase is set to
        `Gtk.PropagationPhase.NONE` to ensure it's not invoked
        anymore.

        NB. The controller is only really removed from the widget when it's destroyed!
            This is a Gtk3 limitation.
        """
        if controller in self._controllers:
            controller.set_propagation_phase(Gtk.PropagationPhase.NONE)
            self._controllers.discard(controller)
            return True
        return False

    def remove_all_controllers(self) -> None:
        """Remove all registered controllers."""
        for controller in set(self._controllers):
            self.remove_controller(controller)

    def zoom(self, factor: float) -> None:
        """Zoom in/out by factor ``factor``."""
        assert self._model
        self.matrix.scale(factor, factor)
        self.request_update((), self._model.get_all_items())

    def get_items_in_rectangle(
        self, rect: Rect, contain: bool = False
    ) -> Iterable[Item]:
        """Return the items in the rectangle 'rect'.

        Items are automatically sorted in model's processing order.
        """
        assert self._model
        items = (
            self._qtree.find_inside(rect)
            if contain
            else self._qtree.find_intersect(rect)
        )
        return self._model.sort(items)

    def get_item_bounding_box(self, item: Item) -> Rectangle:
        """Get the bounding box for the item, in view coordinates."""
        return Rectangle(*self._qtree.get_bounds(item))

    def queue_redraw(self) -> None:
        """Redraw the entire view."""
        self.update_back_buffer()

    def request_update(
        self,
        items: Iterable[Item],
        matrix_only_items: Iterable[Item] = (),
        removed_items: Iterable[Item] = (),
    ) -> None:
        """Request update for items.

        Items will get a full update treatment, while
        ``matrix_only_items`` will only have their bounding box
        recalculated.
        """
        if items:
            self._dirty_items.update(items)
        if matrix_only_items:
            self._dirty_matrix_items.update(matrix_only_items)

        # Remove removed items:
        if removed_items:
            selection = self._selection
            self._dirty_matrix_items.difference_update(removed_items)
            self._dirty_items.difference_update(removed_items)

            for item in removed_items:
                self._qtree.remove(item)
                selection.unselect_item(item)

        self.update()

    @g_async(single=True)
    def update(self) -> None:
        """Update view status according to the items updated in the model."""
        model = self._model
        if not model:
            return

        try:
            dirty_items = self._dirty_items
            dirty_matrix_items = self.all_dirty_matrix_items()
            dirty_items.update(self.update_qtree(dirty_items, dirty_matrix_items))

            model.update_now(dirty_items, dirty_matrix_items)

            self.update_bounding_box(dirty_items)
            self._scrolling.update_adjustments(
                self.get_allocation(), self._qtree.soft_bounds
            )
            self.update_back_buffer()
        finally:
            self._dirty_items.clear()
            self._dirty_matrix_items.clear()

    def all_dirty_matrix_items(self) -> Set[Item]:
        """Recalculate matrices of the items. Items' children matrices are
        recalculated, too.

        Return items, which matrices were recalculated.
        """
        model = self._model
        if not model:
            return set()

        def update_matrices(items: Iterable[Item]) -> Iterable[Item]:
            assert model
            for item in items:
                parent = model.get_parent(item)
                if parent is not None and parent in items:
                    # item's matrix will be updated thanks to parent's matrix update
                    continue

                yield item

                yield from update_matrices(set(model.get_children(item)))

        return set(update_matrices(self._dirty_matrix_items))

    def update_qtree(
        self, dirty_items: Collection[Item], dirty_matrix_items: Iterable[Item]
    ) -> Iterable[Item]:
        for i in dirty_matrix_items:
            if i not in self._qtree:
                yield i
            elif i not in dirty_items:
                # Only matrix has changed, so calculate new bounding box
                # based on quadtree data (= bb in item coordinates).
                bounds = self._qtree.get_data(i)
                i2v = self.get_matrix_i2v(i)
                x, y = i2v.transform_point(bounds[0], bounds[1])
                w, h = i2v.transform_distance(bounds[2], bounds[3])
                vbounds = Rectangle(x, y, w, h)
                self._qtree.add(i, vbounds.tuple(), bounds)

    def update_bounding_box(self, items: Collection[Item]) -> None:
        """Update the bounding boxes of the model items for this view, in model
        coordinates."""
        cr = (
            cairo.Context(self._back_buffer)
            if self._back_buffer
            else instant_cairo_context()
        )

        cr.set_matrix(self.matrix.to_cairo())
        cr.save()
        cr.rectangle(0, 0, 0, 0)
        cr.clip()
        try:
            painter = self._bounding_box_painter
            if items is None:
                items = list(self.model.get_all_items())

            items_and_bounds = painter.paint(items, cr)
            assert items_and_bounds is not None
            for item, bounds in items_and_bounds.items():
                v2i = self.get_matrix_v2i(item)
                ix, iy = v2i.transform_point(bounds.x, bounds.y)
                iw, ih = v2i.transform_distance(bounds.width, bounds.height)
                self._qtree.add(item=item, bounds=bounds.tuple(), data=(ix, iy, iw, ih))
        finally:
            cr.restore()

    @g_async(single=True, priority=GLib.PRIORITY_HIGH_IDLE)
    def update_back_buffer(self) -> None:
        if self.model and self.get_window():
            if not self._back_buffer or self._back_buffer_needs_resizing:
                allocation = self.get_allocation()
                self._back_buffer = self.get_window().create_similar_surface(
                    cairo.Content.COLOR_ALPHA, allocation.width, allocation.height
                )
                self._back_buffer_needs_resizing = False

            assert self._back_buffer
            allocation = self.get_allocation()
            cr = cairo.Context(self._back_buffer)

            cr.save()
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.paint()
            cr.restore()

            Gtk.render_background(
                self.get_style_context(), cr, 0, 0, allocation.width, allocation.height
            )

            items = self.get_items_in_rectangle(
                (0, 0, allocation.width, allocation.height)
            )

            cr.set_matrix(self.matrix.to_cairo())
            cr.save()
            self.painter.paint(list(items), cr)
            cr.restore()

            if DEBUG_DRAW_BOUNDING_BOX:
                for item in self.get_items_in_rectangle(
                    (0, 0, allocation.width, allocation.height)
                ):
                    try:
                        b = self.get_item_bounding_box(item)
                    except KeyError:
                        pass  # No bounding box right now..
                    else:
                        cr.save()
                        cr.identity_matrix()
                        cr.set_source_rgb(0.8, 0, 0)
                        cr.set_line_width(1.0)
                        cr.rectangle(*b)
                        cr.stroke()
                        cr.restore()

            if DEBUG_DRAW_QUADTREE:

                def draw_qtree_bucket(bucket: QuadtreeBucket) -> None:
                    cr.rectangle(*bucket.bounds)
                    cr.stroke()
                    for b in bucket._buckets:
                        draw_qtree_bucket(b)

                cr.set_source_rgb(0, 0, 0.8)
                cr.set_line_width(1.0)
                draw_qtree_bucket(self._qtree._bucket)

            self.get_window().invalidate_rect(allocation, True)

    def do_realize(self) -> None:
        Gtk.DrawingArea.do_realize(self)

        if self._model:
            # Ensure updates are propagated
            self._model.register_view(self)
            self.request_update(self._model.get_all_items())

    def do_unrealize(self) -> None:
        if self._model:
            self._model.unregister_view(self)

        self._qtree.clear()

        self._dirty_items.clear()
        self._dirty_matrix_items.clear()

        Gtk.DrawingArea.do_unrealize(self)

    def do_configure_event(self, event: Gdk.EventConfigure) -> bool:
        allocation = self.get_allocation()
        self._scrolling.update_adjustments(allocation, self._qtree.soft_bounds)
        self._qtree.resize((0, 0, allocation.width, allocation.height))
        if self.get_window():
            self._back_buffer_needs_resizing = True
            self.update_back_buffer()
        else:
            self._back_buffer = None

        return False

    def do_draw(self, cr: cairo.Context) -> bool:
        if not self._model:
            return False

        if not self._back_buffer:
            return False

        cr.set_source_surface(self._back_buffer, 0, 0)
        cr.paint()

        return False
