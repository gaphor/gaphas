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
from gaphas.painter import DefaultPainter, ItemPainter
from gaphas.painter.boundingboxpainter import CairoBoundingBoxContext
from gaphas.painter.painter import ItemPainterType, Painter
from gaphas.quadtree import Quadtree, QuadtreeBucket
from gaphas.view.model import Model
from gaphas.view.scrolling import Scrolling
from gaphas.view.selection import Selection

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = (
    Gdk.CursorType.LEFT_PTR
    if Gtk.get_major_version() == 3
    else Gdk.Cursor.new_from_name("default")
)


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

        self._back_buffer: Optional[cairo.Surface] = None
        self._back_buffer_needs_resizing = True

        self._controllers: Set[Gtk.EventController] = set()

        self.set_can_focus(True)
        if Gtk.get_major_version() == 3:
            self.add_events(
                Gdk.EventMask.BUTTON_PRESS_MASK
                | Gdk.EventMask.BUTTON_RELEASE_MASK
                | Gdk.EventMask.POINTER_MOTION_MASK
                | Gdk.EventMask.KEY_PRESS_MASK
                | Gdk.EventMask.KEY_RELEASE_MASK
                | Gdk.EventMask.SCROLL_MASK
                | Gdk.EventMask.STRUCTURE_MASK
            )
            self.set_app_paintable(True)
        else:
            self.set_draw_func(GtkView.do_draw)
            self.connect_after("resize", GtkView.on_resize)

        def alignment_updated(matrix: Matrix) -> None:
            if self._model:
                self._matrix *= matrix  # type: ignore[misc]

        self._scrolling = Scrolling(alignment_updated)

        self._selection = selection or Selection()

        self._matrix = Matrix()
        self._painter: Painter = DefaultPainter(self)
        self._bounding_box_painter: ItemPainterType = ItemPainter(self._selection)
        self._matrix_changed = False

        self._qtree: Quadtree[Item, Tuple[float, float, float, float]] = Quadtree()

        self._model: Optional[Model] = None
        if model:
            self.model = model

        self._selection.add_handler(self.on_selection_update)
        self._matrix.add_handler(self.on_matrix_update)

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
    def bounding_box_painter(self) -> ItemPainterType:
        """Special painter for calculating item bounding boxes."""
        return self._bounding_box_painter

    @bounding_box_painter.setter
    def bounding_box_painter(self, painter: ItemPainterType) -> None:
        self._bounding_box_painter = painter

    @property
    def selection(self) -> Selection:
        """Selected, focused and hovered items."""
        return self._selection

    @selection.setter
    def selection(self, selection: Selection) -> None:
        """Selected, focused and hovered items."""
        self._selection = selection
        if self._model:
            self.request_update(self._model.get_all_items())

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
        if Gtk.get_major_version() != 3:
            for controller in controllers:
                super().add_controller(controller)
        self._controllers.update(controllers)

    def remove_controller(self, controller: Gtk.EventController) -> bool:
        """Remove a controller.

        The event controller's propagation phase is set to
        `Gtk.PropagationPhase.NONE` to ensure it's not invoked
        anymore.

        NB. The controller is only really removed from the widget when it's destroyed!
            This is a Gtk3 limitation.
        """
        if Gtk.get_major_version() != 3:
            super().remove_controller(controller)
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
        self.request_update(self._model.get_all_items())

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

    def request_update(
        self,
        items: Iterable[Item],
        removed_items: Iterable[Item] = (),
    ) -> None:
        """Request update for items."""
        if items:
            self._dirty_items.update(items)

        if removed_items:
            selection = self._selection
            self._dirty_items.difference_update(removed_items)

            for item in removed_items:
                self._qtree.remove(item)
                selection.unselect_item(item)

        if items or removed_items:
            self.update()

    @g_async(single=True)
    def update(self) -> None:
        """Update view status according to the items updated in the model."""
        model = self._model
        if not model:
            return

        dirty_items = self.all_dirty_items()
        model.update_now(dirty_items)

        dirty_items |= self.all_dirty_items()
        self.update_bounding_box(dirty_items)

        allocation = self.get_allocation()
        self._scrolling.update_adjustments(
            allocation.width, allocation.height, self._qtree.soft_bounds
        )
        self.update_back_buffer()

    def all_dirty_items(self) -> Set[Item]:
        """Return all dirty items, clearing the marked items."""
        model = self._model
        if not model:
            return set()

        def iterate_items(items: Iterable[Item]) -> Iterable[Item]:
            assert model
            for item in items:
                parent = model.get_parent(item)
                if parent is not None and parent in items:
                    # item's matrix will be updated thanks to parent's matrix update
                    continue

                yield item

                yield from iterate_items(set(model.get_children(item)))

        dirty_items = set(iterate_items(self._dirty_items))
        self._dirty_items.clear()
        return dirty_items

    def update_bounding_box(self, items: Collection[Item]) -> None:
        """Update the bounding boxes of the model items for this view, in model
        coordinates."""
        painter = self._bounding_box_painter
        qtree = self._qtree
        c2v = self._matrix
        cr = (
            cairo.Context(self._back_buffer)
            if self._back_buffer
            else instant_cairo_context()
        )

        for item in items:
            bbctx = CairoBoundingBoxContext(cr)
            painter.paint_item(item, bbctx)
            bb = bbctx.get_bounds()
            v2i = self.get_matrix_v2i(item)
            ix, iy = v2i.transform_point(bb.x, bb.y)
            iw, ih = v2i.transform_distance(bb.width, bb.height)
            self._qtree.add(item=item, bounds=bb.tuple(), data=(ix, iy, iw, ih))

        if self._matrix_changed and self._model:
            for item in self._model.get_all_items():
                if item not in items:
                    bounds = self._qtree.get_data(item)
                    x, y = c2v.transform_point(bounds[0], bounds[1])
                    w, h = c2v.transform_distance(bounds[2], bounds[3])
                    qtree.add(item=item, bounds=(x, y, w, h), data=bounds)
            self._matrix_changed = False

    @g_async(single=True, priority=GLib.PRIORITY_HIGH_IDLE)
    def update_back_buffer(self) -> None:
        if Gtk.get_major_version() == 3:
            surface = self.get_window()
        else:
            surface = self.get_native() and self.get_native().get_surface()

        if self.model and surface:
            allocation = self.get_allocation()
            width = allocation.width
            height = allocation.height

            if not self._back_buffer or self._back_buffer_needs_resizing:
                self._back_buffer = surface.create_similar_surface(
                    cairo.Content.COLOR_ALPHA, width, height
                )
                self._back_buffer_needs_resizing = False

            assert self._back_buffer
            cr = cairo.Context(self._back_buffer)

            cr.save()
            cr.set_operator(cairo.OPERATOR_CLEAR)
            cr.paint()
            cr.restore()

            Gtk.render_background(self.get_style_context(), cr, 0, 0, width, height)

            items = self.get_items_in_rectangle((0, 0, width, height))

            cr.set_matrix(self.matrix.to_cairo())
            cr.save()
            self.painter.paint(list(items), cr)
            cr.restore()

            if DEBUG_DRAW_BOUNDING_BOX:
                for item in self.get_items_in_rectangle((0, 0, width, height)):
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

            if Gtk.get_major_version() == 3:
                self.get_window().invalidate_rect(allocation, True)
            else:
                self.queue_draw()

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

        Gtk.DrawingArea.do_unrealize(self)

    def do_configure_event(self, event: Gdk.EventConfigure) -> bool:
        # GTK+ 3 only
        allocation = self.get_allocation()
        self.on_resize(allocation.width, allocation.height)

        return False

    def on_selection_update(self, item: Optional[Item]) -> None:
        if self._model:
            if item is None:
                self.request_update(self._model.get_all_items())
            elif item in self._model.get_all_items():
                self.request_update((item,))

    def on_matrix_update(self, matrix, old_matrix_values):
        if not self._matrix_changed:
            self._matrix_changed = True
            self.update()

    def on_resize(self, width: int, height: int) -> None:
        self._qtree.resize((0, 0, width, height))
        self._scrolling.update_adjustments(width, height, self._qtree.soft_bounds)
        if self.get_realized():
            self._back_buffer_needs_resizing = True
            self.update_back_buffer()
        else:
            self._back_buffer = None

    def do_draw(self, cr: cairo.Context, width: int = 0, height: int = 0) -> bool:
        if not self._model:
            return False

        if not self._back_buffer:
            return False

        cr.set_source_surface(self._back_buffer, 0, 0)
        cr.paint()

        return False
