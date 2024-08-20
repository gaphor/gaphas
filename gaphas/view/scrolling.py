from __future__ import annotations

from math import isclose
from typing import Callable

from gi.repository import Gtk

from gaphas.geometry import Rectangle


class Scrolling:
    """Contains Gtk.Adjustment and related code."""

    def __init__(
        self, scrolling_updated: Callable[[float | None, float | None], None]
    ) -> None:
        self._scrolling_updated = scrolling_updated
        self.hadjustment: Gtk.Adjustment | None = None
        self.vadjustment: Gtk.Adjustment | None = None
        self.hscroll_policy: Gtk.ScrollablePolicy | None = None
        self.vscroll_policy: Gtk.ScrollablePolicy | None = None
        self._hadjustment_handler_id = 0
        self._vadjustment_handler_id = 0

    def get_property(self, prop):
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
        if prop.name == "hadjustment":
            if value is not None:
                if self.hadjustment and self._hadjustment_handler_id:
                    self.hadjustment.disconnect(self._hadjustment_handler_id)
                self.hadjustment = value
                self._hadjustment_handler_id = self.hadjustment.connect(
                    "value-changed", self.on_hadjustment_changed
                )
        elif prop.name == "vadjustment":
            if value is not None:
                if self.vadjustment and self._vadjustment_handler_id:
                    self.vadjustment.disconnect(self._vadjustment_handler_id)
                self.vadjustment = value
                self._vadjustment_handler_id = self.vadjustment.connect(
                    "value-changed", self.on_vadjustment_changed
                )
        elif prop.name == "hscroll-policy":
            self.hscroll_policy = value
        elif prop.name == "vscroll-policy":
            self.vscroll_policy = value
        else:
            raise AttributeError(f"Unknown property {prop.name}")

    def update_position(self, x: float, y: float) -> None:
        if self.hadjustment and not isclose(self.hadjustment.get_value(), x):
            self.hadjustment.handler_block(self._hadjustment_handler_id)
            self.hadjustment.set_value(-x)
            self.hadjustment.handler_unblock(self._hadjustment_handler_id)

        if self.vadjustment and not isclose(self.vadjustment.get_value(), y):
            self.vadjustment.handler_block(self._vadjustment_handler_id)
            self.vadjustment.set_value(-y)
            self.vadjustment.handler_unblock(self._vadjustment_handler_id)

    def update_adjustments(self, width: int, height: int, bounds: Rectangle) -> None:
        """Update scroll bar values (adjustments in GTK).

        The value will change when a scroll bar is moved.
        """
        # canvas limits (in view coordinates)
        c = Rectangle(*bounds)
        c.expand(min(width, height) / 2)
        u = c + Rectangle(width=width, height=height)

        if self.hadjustment:
            self.hadjustment.set_lower(u.x)
            self.hadjustment.set_upper(u.x1)
            self.hadjustment.set_step_increment(width // 10)
            self.hadjustment.set_page_increment(width)
            self.hadjustment.set_page_size(width)

        if self.vadjustment:
            self.vadjustment.set_lower(u.y)
            self.vadjustment.set_upper(u.y1)
            self.vadjustment.set_step_increment(height // 10)
            self.vadjustment.set_page_increment(height)
            self.vadjustment.set_page_size(height)

    def on_hadjustment_changed(self, adj):
        self._scrolling_updated(-adj.get_value(), None)

    def on_vadjustment_changed(self, adj):
        self._scrolling_updated(None, -adj.get_value())
