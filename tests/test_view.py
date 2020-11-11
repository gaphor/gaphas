"""Test cases for the View class."""

import pytest
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.view import GtkView


@pytest.fixture(autouse=True)
def main_loop(window, box):
    while Gtk.events_pending():
        Gtk.main_iteration()


def test_get_item_at_point(view, box):
    """Hover tool only reacts on motion-notify events."""
    box.width = 50
    box.height = 50

    assert view.get_item_at_point((10, 10)) is box
    assert view.get_item_at_point((60, 10)) is None


def test_get_unselected_item_at_point(view, box):
    box.width = 50
    box.height = 50
    view.selection.select_items(box)

    assert view.get_item_at_point((10, 10)) is box
    assert view.get_item_at_point((10, 10), selected=False) is None


def test_item_removal(view, canvas, box):
    assert len(list(canvas.get_all_items())) == len(view._qtree)

    view.selection.set_focused_item(box)
    canvas.remove(box)

    assert len(list(canvas.get_all_items())) == 0
    assert len(view._qtree) == 0


def test_view_registration():
    canvas = Canvas()

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


def test_view_registration_2(view, canvas, window):
    """Test view registration and destroy when view is destroyed."""
    assert len(canvas._registered_views) == 1
    assert view in canvas._registered_views

    window.destroy()

    assert len(canvas._registered_views) == 0


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
