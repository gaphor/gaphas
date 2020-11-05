from typing import Optional

from gi.repository import Gtk

from gaphas.decorators import AsyncIO
from gaphas.geometry import Rectangle
from gaphas.matrix import Matrix


class Scrolling:
    """Contains Gtk.Adjustment and related code."""

    def __init__(self, scrolling_updated):
        """
        Initialize the gtk3 handler.

        Args:
            self: (todo): write your description
            scrolling_updated: (todo): write your description
        """
        self._scrolling_updated = scrolling_updated
        self.hadjustment: Optional[Gtk.Adjustment] = None
        self.vadjustment: Optional[Gtk.Adjustment] = None
        self.hscroll_policy: Optional[Gtk.ScrollablePolicy] = None
        self.vscroll_policy: Optional[Gtk.ScrollablePolicy] = None
        self._hadjustment_handler_id = 0
        self._vadjustment_handler_id = 0

    def get_property(self, prop):
        """
        Retrieves property of a property.

        Args:
            self: (todo): write your description
            prop: (str): write your description
        """
        if prop.name == "hadjustment":
            return self.hadjustment
        elif prop.name == "vadjustment":
            return self.vadjustment
        elif prop.name == "hscroll-policy":
            return self.hscroll_policy
        elif prop.name == "vscroll-policy":
            return self.vscroll_policy
        else:
            raise AttributeError(f"Unknown property {prop.name}")

    def set_property(self, prop, value):
        """
        Set the property of the actor.

        Args:
            self: (todo): write your description
            prop: (todo): write your description
            value: (todo): write your description
        """
        if prop.name == "hadjustment":
            if value is not None:
                self.hadjustment = value
                self.hadjustment_handler_id = self.hadjustment.connect(
                    "value-changed", self.on_adjustment_changed
                )
                self._scrolling_updated(Matrix())
        elif prop.name == "vadjustment":
            if value is not None:
                self.vadjustment = value
                self.vadjustment_handler_id = self.vadjustment.connect(
                    "value-changed", self.on_adjustment_changed
                )
                self._scrolling_updated(Matrix())
        elif prop.name == "hscroll-policy":
            self.hscroll_policy = value
        elif prop.name == "vscroll-policy":
            self.vscroll_policy = value
        else:
            raise AttributeError(f"Unknown property {prop.name}")

    @AsyncIO(single=True)
    def update_adjustments(self, allocation, bounds):
        """
        Updates all adjustments in the region.

        Args:
            self: (todo): write your description
            allocation: (str): write your description
            bounds: (todo): write your description
        """
        aw, ah = allocation.width, allocation.height

        # canvas limits (in view coordinates)
        c = Rectangle(*bounds)

        # view limits
        v = Rectangle(0, 0, aw, ah)

        # union of these limits gives scrollbar limits
        u = c if v in c else c + v
        if not self.hadjustment:
            self._hadjustment = Gtk.Adjustment.new(
                value=v.x,
                lower=u.x,
                upper=u.x1,
                step_increment=aw // 10,
                page_increment=aw,
                page_size=aw,
            )
        else:
            self.hadjustment.set_value(v.x)
            self.hadjustment.set_lower(u.x)
            self.hadjustment.set_upper(u.x1)
            self.hadjustment.set_step_increment(aw // 10)
            self.hadjustment.set_page_increment(aw)
            self.hadjustment.set_page_size(aw)

        if not self.vadjustment:
            self.vadjustment = Gtk.Adjustment.new(
                value=v.y,
                lower=u.y,
                upper=u.y1,
                step_increment=ah // 10,
                page_increment=ah,
                page_size=ah,
            )
        else:
            self.vadjustment.set_value(v.y)
            self.vadjustment.set_lower(u.y)
            self.vadjustment.set_upper(u.y1)
            self.vadjustment.set_step_increment(ah // 10)
            self.vadjustment.set_page_increment(ah)
            self.vadjustment.set_page_size(ah)

    def on_adjustment_changed(self, adj):
        """Change the transformation matrix of the view to reflect the value of
        the x/y adjustment (scrollbar)."""
        value = adj.get_value()
        if value == 0.0:
            return

        # Can not use self._matrix.translate(-value , 0) here, since
        # the translate method effectively does a m * self._matrix, which
        # will result in the translation being multiplied by the orig. matrix
        m = Matrix()
        if adj is self.hadjustment:
            m.translate(-value, 0)
        elif adj is self.vadjustment:
            m.translate(0, -value)

        self._scrolling_updated(m)
