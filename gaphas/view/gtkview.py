"""This module contains everything to display a model on a screen."""
from __future__ import annotations

from typing import Collection, Iterable

import cairo
from gi.repository import Gdk, GLib, GObject, Gtk

from gaphas.decorators import g_async
from gaphas.geometry import Rect, Rectangle
from gaphas.item import Item
from gaphas.matrix import Matrix
from gaphas.model import Model
from gaphas.painter import DefaultPainter, ItemPainter
from gaphas.painter.painter import ItemPainterType, Painter
from gaphas.quadtree import Quadtree, QuadtreeBucket
from gaphas.selection import Selection
from gaphas.view.scrolling import Scrolling

# Handy debug flag for drawing bounding boxes around the items.
DEBUG_DRAW_BOUNDING_BOX = False
DEBUG_DRAW_QUADTREE = False

# The default cursor (use in case of a cursor reset)
DEFAULT_CURSOR = (
    Gdk.CursorType.LEFT_PTR
    if Gtk.get_major_version() == 3
    else Gdk.Cursor.new_from_name("default")
)

# The tolerance for Cairo. Bigger values increase speed and reduce accuracy
# (default: 0.1)
PAINT_TOLERANCE = 0.8
BOUNDING_BOX_TOLERANCE = 1.0


class GtkView(Gtk.DrawingArea, Gtk.Scrollable):
    """GTK+ widget for rendering a gaphas.model.Model to a screen.  The view
    uses Tools to handle events and Painters to draw. Both are configurable.

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

    def __init__(self, model: Model | None = None, selection: Selection = None):
        """Create a new view.

        Args:
            model (Model): optional model to be set on construction time.
            selection (Selection): optional selection object, in case the default
                selection object (hover/select/focus) is not enough.
        """
        super().__init__()

        self._dirty_items: set[Item] = set()

        self._back_buffer: cairo.Surface | None = None
        self._back_buffer_needs_resizing = True

        self._controllers: set[Gtk.EventController] = set()

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
                | Gdk.EventMask.SMOOTH_SCROLL_MASK
            )
            self.set_app_paintable(True)
        else:
            self.set_focusable(True)
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

        # quadtree bounds are in canvas coordinates (not view!)
        self._qtree: Quadtree[Item, None] = Quadtree()

        self._model: Model | None = None
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
    def model(self) -> Model | None:
        """The model."""
        return self._model

    @model.setter
    def model(self, model: Model | None) -> None:
        if self._model:
            self._model.unregister_view(self)
            self._selection.clear()
            self._dirty_items.clear()
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
        return Rectangle(*transform_rectangle(self._matrix, self._qtree.soft_bounds))

    @property
    def hadjustment(self) -> Gtk.Adjustment:
        """Gtk adjustment object for use with a scrollbar."""
        return self._scrolling.hadjustment

    @property
    def vadjustment(self) -> Gtk.Adjustment:
        """Gtk adjustment object for use with a scrollbar."""
        return self._scrolling.vadjustment

    def clamp_item(self, item):
        """Update adjustments so the item is located inside the view port."""
        x, y, w, h = self.get_item_bounding_box(item).tuple()
        self.hadjustment.clamp_page(x, x + w)
        self.vadjustment.clamp_page(y, y + h)

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
        """Return the items in the rectangle 'rect' (in view coordinates).

        Items are automatically sorted in model's processing order.
        """
        assert self._model
        crect = transform_rectangle(self._matrix.inverse(), rect)
        items = (
            self._qtree.find_inside(crect)
            if contain
            else self._qtree.find_intersect(crect)
        )
        return self._model.sort(items)

    def get_item_bounding_box(self, item: Item) -> Rectangle:
        """Get the bounding box for the item, in view coordinates."""
        return Rectangle(
            *transform_rectangle(self._matrix, self._qtree.get_bounds(item))
        )

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

        old_bb = self._qtree.soft_bounds
        self.update_bounding_box(dirty_items)
        if self._qtree.soft_bounds != old_bb:
            self.update_scrolling()
        self.update_back_buffer()

    def all_dirty_items(self) -> set[Item]:
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
        for item in items:
            surface = cairo.RecordingSurface(cairo.Content.COLOR_ALPHA, None)  # type: ignore[arg-type]
            cr = cairo.Context(surface)
            cr.set_tolerance(BOUNDING_BOX_TOLERANCE)

            painter.paint_item(item, cr)
            x, y, w, h = surface.ink_extents()

            qtree.add(item=item, bounds=(x, y, w, h))

    @g_async(single=True)
    def update_scrolling(self) -> None:
        allocation = self.get_allocation()
        self._scrolling.update_adjustments(
            allocation.width, allocation.height, self.bounding_box
        )

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

            cr.set_matrix(self.matrix.to_cairo())
            cr.save()
            cr.set_tolerance(PAINT_TOLERANCE)
            items = self.get_items_in_rectangle((0, 0, width, height))
            self.painter.paint(list(items), cr)
            cr.restore()

            if DEBUG_DRAW_BOUNDING_BOX:
                self._debug_draw_bounding_box(cr, width, height)

            if DEBUG_DRAW_QUADTREE:
                self._debug_draw_quadtree(cr)

            if Gtk.get_major_version() == 3:
                self.get_window().invalidate_rect(allocation, True)
            else:
                self.queue_draw()

    def _debug_draw_bounding_box(self, cr, width, height):
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

    def _debug_draw_quadtree(self, cr):
        def draw_qtree_bucket(bucket: QuadtreeBucket) -> None:
            cr.rectangle(*bucket.bounds)
            cr.stroke()
            for b in bucket._buckets:
                draw_qtree_bucket(b)

        cr.set_source_rgb(0, 0, 0.8)
        cr.set_line_width(1.0)
        draw_qtree_bucket(self._qtree._bucket)

    def do_realize(self) -> None:
        Gtk.DrawingArea.do_realize(self)

        if self._model:
            # Ensure updates are propagated
            self._model.register_view(self)
            self.request_update(self._model.get_all_items())

    def do_unrealize(self) -> None:
        if self._model:
            self.model = None

        Gtk.DrawingArea.do_unrealize(self)

    def do_configure_event(self, event: Gdk.EventConfigure) -> bool:
        # GTK+ 3 only
        allocation = self.get_allocation()
        self.on_resize(allocation.width, allocation.height)

        return False

    def on_selection_update(self, item: Item | None) -> None:
        if self._model:
            if item is None:
                self.request_update(self._model.get_all_items())
            elif item in self._model.get_all_items():
                self.request_update((item,))

    def on_matrix_update(self, matrix, old_matrix_values):
        # Test if scale or rotation changed
        if tuple(matrix)[:4] != old_matrix_values[:4]:
            self.update_scrolling()
        self.update_back_buffer()

    def on_resize(self, _width: int, _height: int) -> None:
        self.update_scrolling()
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


def transform_rectangle(matrix: Matrix, rect: Rect) -> Rect:
    x, y, w, h = rect

    return matrix.transform_point(x, y) + matrix.transform_distance(w, h)
