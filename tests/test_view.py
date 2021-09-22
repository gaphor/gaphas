"""Test cases for the View class."""

import pytest
from gi.repository import GLib, Gtk

from gaphas.canvas import Canvas
from gaphas.view import GtkView, Selection


@pytest.fixture(autouse=True)
def main_loop(window, box):
    ctx = GLib.main_context_default()
    while ctx.pending():
        ctx.iteration()


class CustomSelection(Selection):
    pass


def test_custom_selection():
    custom_selection = CustomSelection()
    view = GtkView(selection=custom_selection)

    assert view.selection is custom_selection


def test_custom_selection_setter():
    custom_selection = CustomSelection()
    view = GtkView()

    view.selection = custom_selection

    assert view.selection is custom_selection


def test_item_removal(view, canvas, box):
    assert len(list(canvas.get_all_items())) == len(view._qtree)

    view.selection.focused_item = box
    canvas.remove(box)

    assert len(list(canvas.get_all_items())) == 0
    assert len(view._qtree) == 0


def test_view_registration():
    canvas = Canvas()

    # GTK view does register for updates though

    view = GtkView(canvas)
    assert len(canvas._registered_views) == 1

    if Gtk.get_major_version() == 3:
        window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        window.add(view)
        window.show_all()
    else:
        window = Gtk.Window.new()
        window.set_child(view)

    view.model = None
    assert len(canvas._registered_views) == 0

    view.model = canvas
    assert len(canvas._registered_views) == 1


@pytest.mark.skipif(Gtk.get_major_version() != 3, reason="Works only for GTK+ 3")
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
    sc.add(view) if Gtk.get_major_version() == 3 else sc.set_child(view)
    view.update()
    return view, sc


@pytest.mark.skipif(Gtk.get_major_version() != 3, reason="Works only for GTK+ 3")
def test_scroll_adjustments_signal(sc_view):
    assert sc_view[0].hadjustment
    assert sc_view[0].vadjustment
    assert sc_view[0].hadjustment.get_value() == 0.0
    assert sc_view[0].hadjustment.get_lower() == -0.5
    assert sc_view[0].hadjustment.get_upper() == 1.0
    assert sc_view[0].hadjustment.get_step_increment() == 0.0
    assert sc_view[0].hadjustment.get_page_increment() == 1.0
    assert sc_view[0].hadjustment.get_page_size() == 1.0
    assert sc_view[0].vadjustment.get_value() == 0.0
    assert sc_view[0].vadjustment.get_lower() == -0.5
    assert sc_view[0].vadjustment.get_upper() == 1.0
    assert sc_view[0].vadjustment.get_step_increment() == 0.0
    assert sc_view[0].vadjustment.get_page_increment() == 1.0
    assert sc_view[0].vadjustment.get_page_size() == 1.0


def test_scroll_adjustments(sc_view):
    assert sc_view[1].get_hadjustment() is sc_view[0].hadjustment
    assert sc_view[1].get_vadjustment() is sc_view[0].vadjustment


def test_will_not_remove_lone_controller(view):
    ctrl = (
        Gtk.EventControllerMotion.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerMotion.new()
    )

    removed = view.remove_controller(ctrl)

    assert not removed


def test_can_add_and_remove_controller(view):
    ctrl = (
        Gtk.EventControllerMotion.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerMotion.new()
    )
    view.add_controller(ctrl)

    removed = view.remove_controller(ctrl)

    assert removed
    assert ctrl.get_propagation_phase() == Gtk.PropagationPhase.NONE


def test_can_remove_all_controllers(view):
    ctrl = (
        Gtk.EventControllerMotion.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.EventControllerMotion.new()
    )
    view.add_controller(ctrl)

    view.remove_all_controllers()

    assert ctrl.get_propagation_phase() == Gtk.PropagationPhase.NONE
