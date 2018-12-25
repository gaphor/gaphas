"""Test cases for the View class.

"""
from __future__ import division

import math

import pytest
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Line
from gaphas.view import View, GtkView


class ViewFixture(object):
    def __init__(self):
        self.canvas = Canvas()
        self.view = GtkView(self.canvas)
        self.window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        self.window.add(self.view)
        self.window.show_all()

        self.box = Box()
        self.canvas.add(self.box)
        # No gtk main loop, so updates occur instantly
        assert not self.canvas.require_update()

        # Process pending (expose) events, which cause the canvas to be drawn.
        while Gtk.events_pending():
            Gtk.main_iteration()


@pytest.fixture()
def view_fixture():
    return ViewFixture()


def test_bounding_box_calculations(view_fixture):
    """A view created before and after the canvas is populated should contain
    the same data.

    """
    view_fixture.view.realize()
    view_fixture.box.matrix = (1.0, 0.0, 0.0, 1, 10, 10)

    line = Line()
    line.fuzziness = 1
    line.handles()[1].pos = (30, 30)
    line.matrix.translate(30, 60)
    view_fixture.canvas.add(line)

    window2 = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    view2 = GtkView(canvas=view_fixture.canvas)
    window2.add(view2)
    window2.show_all()

    # Process pending (expose) events, which cause the canvas to be drawn.
    while Gtk.events_pending():
        Gtk.main_iteration()

    try:
        assert view2.get_item_bounding_box(view_fixture.box)
        assert view_fixture.view.get_item_bounding_box(view_fixture.box)
        assert view_fixture.view.get_item_bounding_box(
            view_fixture.box
        ) == view2.get_item_bounding_box(view_fixture.box), (
            "%s != %s"
            % (
                view_fixture.view.get_item_bounding_box(view_fixture.box),
                view2.get_item_bounding_box(view_fixture.box),
            )
        )
        assert view_fixture.view.get_item_bounding_box(
            line
        ) == view2.get_item_bounding_box(line), (
            "%s != %s"
            % (
                view_fixture.view.get_item_bounding_box(line),
                view2.get_item_bounding_box(line),
            )
        )
    finally:
        view_fixture.window.destroy()
        window2.destroy()


def test_get_item_at_point(view_fixture):
    """Hover tool only reacts on motion-notify events.

    """
    view_fixture.box.width = 50
    view_fixture.box.height = 50
    assert len(view_fixture.view._qtree._ids) == 1
    assert not view_fixture.view._qtree._bucket.bounds == (
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
    box.matrix.translate(20, 20)
    box.matrix.rotate(math.pi / 2)

    i, h = view_fixture.view.get_handle_at_point((20, 20))
    assert i is box
    assert h is box.handles()[0]


def test_item_removal(view_fixture):
    assert len(view_fixture.canvas.get_all_items()) == len(view_fixture.view._qtree)

    view_fixture.view.focused_item = view_fixture.box
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

    # By default no complex updating/calculations are done:
    assert view not in box._matrix_i2v
    assert view not in box._matrix_v2i

    # GTK view does register for updates though

    view = GtkView(canvas)
    assert len(canvas._registered_views) == 1

    # No entry, since GtkView is not realized and has no window
    assert view not in box._matrix_i2v
    assert view not in box._matrix_v2i

    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.add(view)
    window.show_all()

    # Now everything is realized and updated
    assert view in box._matrix_i2v
    assert view in box._matrix_v2i

    view.canvas = None
    assert len(canvas._registered_views) == 0

    assert view not in box._matrix_i2v
    assert view not in box._matrix_v2i

    view.canvas = canvas
    assert len(canvas._registered_views) == 1

    assert view in box._matrix_i2v
    assert view in box._matrix_v2i


def test_view_registration_2(view_fixture):
    """Test view registration and destroy when view is destroyed.

    """
    assert hasattr(view_fixture.box, "_matrix_i2v")
    assert hasattr(view_fixture.box, "_matrix_v2i")

    assert view_fixture.box._matrix_i2v[view_fixture.view]
    assert view_fixture.box._matrix_v2i[view_fixture.view]

    assert len(view_fixture.canvas._registered_views) == 1
    assert view_fixture.view in view_fixture.canvas._registered_views

    view_fixture.window.destroy()

    assert len(view_fixture.canvas._registered_views) == 0

    assert view_fixture.view not in view_fixture.box._matrix_i2v
    assert view_fixture.view not in view_fixture.box._matrix_v2i


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
