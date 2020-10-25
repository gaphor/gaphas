"""Test cases for the View class."""
import math

import pytest
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.item import Element as Box
from gaphas.view import GtkView, View


class ViewFixture:
    def __init__(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        self.window.add(self.view)
        self.window.show_all()

        self.box = Box()
        self.canvas.add(self.box)

        # Process pending (expose) events, which cause the canvas to be drawn.
        while Gtk.events_pending():
            Gtk.main_iteration()


@pytest.fixture()
def view_fixture():
    return ViewFixture()


def test_get_item_at_point(view_fixture):
    """Hover tool only reacts on motion-notify events."""
    view_fixture.box.width = 50
    view_fixture.box.height = 50
    assert len(view_fixture.view._qtree._ids) == 1
    assert view_fixture.view._qtree._bucket.bounds != (
        0,
        0,
        0,
        0,
    ), view_fixture.view._qtree._bucket.bounds

    assert view_fixture.view.get_item_at_point((10, 10)) is view_fixture.box
    assert view_fixture.view.get_item_at_point((60, 10)) is None

    view_fixture.window.destroy()


def test_get_handle_at_point(view_fixture):
    box = Box()
    box.min_width = 20
    box.min_height = 30
    box.matrix.translate(20, 20)
    box.matrix.rotate(math.pi / 1.5)
    view_fixture.canvas.add(box)

    i, h = view_fixture.view.get_handle_at_point((20, 20))
    assert i is box
    assert h is box.handles()[0]


def test_get_handle_at_point_at_pi_div_2(view_fixture):
    box = Box()
    box.min_width = 20
    box.min_height = 30
    box.matrix.translate(20, 20)
    box.matrix.rotate(math.pi / 2)
    view_fixture.canvas.add(box)

    i, h = view_fixture.view.get_handle_at_point((20, 20))
    assert i is box
    assert h is box.handles()[0]


def test_item_removal(view_fixture):
    assert len(view_fixture.canvas.get_all_items()) == len(view_fixture.view._qtree)

    view_fixture.view.selection.set_focused_item(view_fixture.box)
    view_fixture.canvas.remove(view_fixture.box)

    assert len(view_fixture.canvas.get_all_items()) == 0
    assert len(view_fixture.view._qtree) == 0

    view_fixture.window.destroy()


def test_view_registration(view_fixture):
    canvas = Canvas()

    # Simple views do not register on the canvas

    view = View(canvas)
    assert len(canvas._registered_views) == 0

    box = Box()
    canvas.add(box)

    # GTK view does register for updates though

    view = GtkView(canvas)
    assert len(canvas._registered_views) == 1

    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.add(view)
    window.show_all()

    view.canvas = None
    assert len(canvas._registered_views) == 0

    view.canvas = canvas
    assert len(canvas._registered_views) == 1


def test_view_registration_2(view_fixture):
    """Test view registration and destroy when view is destroyed."""
    assert len(view_fixture.canvas._registered_views) == 1
    assert view_fixture.view in view_fixture.canvas._registered_views

    view_fixture.window.destroy()

    assert len(view_fixture.canvas._registered_views) == 0


@pytest.fixture()
def sc_view():
    sc = Gtk.ScrolledWindow()
    view = GtkView(Canvas())
    sc.add(view)
    return view, sc


def test_scroll_adjustments_signal(sc_view):
    assert sc_view[0].hadjustment
    assert sc_view[0].vadjustment
    assert sc_view[0].hadjustment.get_value() == 0.0
    assert sc_view[0].hadjustment.get_lower() == 0.0
    assert sc_view[0].hadjustment.get_upper() == 1.0
    assert sc_view[0].hadjustment.get_step_increment() == 0.0
    assert sc_view[0].hadjustment.get_page_increment() == 1.0
    assert sc_view[0].hadjustment.get_page_size() == 1.0
    assert sc_view[0].vadjustment.get_value() == 0.0
    assert sc_view[0].vadjustment.get_lower() == 0.0
    assert sc_view[0].vadjustment.get_upper() == 1.0
    assert sc_view[0].vadjustment.get_step_increment() == 0.0
    assert sc_view[0].vadjustment.get_page_increment() == 1.0
    assert sc_view[0].vadjustment.get_page_size() == 1.0


def test_scroll_adjustments(sc_view):
    assert sc_view[1].get_hadjustment() is sc_view[0].hadjustment
    assert sc_view[1].get_vadjustment() is sc_view[0].vadjustment
