"""Test cases for the View class."""

from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.selection import Selection
from gaphas.view import GtkView


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

    assert not list(canvas.get_all_items())
    assert len(view._qtree) == 0


def test_view_registration():
    canvas = Canvas()

    # GTK view does register for updates though

    view = GtkView(canvas)
    assert len(canvas._registered_views) == 1

    window = Gtk.Window.new()
    window.set_child(view)

    view.model = None
    assert len(canvas._registered_views) == 0

    view.model = canvas
    assert len(canvas._registered_views) == 1


def test_view_registration_2(view, canvas, window):
    """Test view registration and destroy when view is destroyed."""
    window.present()

    assert len(canvas._registered_views) == 1
    assert view in canvas._registered_views

    window.destroy()

    assert len(canvas._registered_views) == 0


def test_scroll_adjustments_signal(view, scrolled_window):
    assert view.hadjustment
    assert view.vadjustment
    assert view.hadjustment.get_value() == 0.0
    assert view.hadjustment.get_lower() == 0.0
    assert view.hadjustment.get_upper() == 0.0
    assert view.hadjustment.get_step_increment() == 0.0
    assert view.hadjustment.get_page_increment() == 0.0
    assert view.hadjustment.get_page_size() == 0.0
    assert view.vadjustment.get_value() == 0.0
    assert view.vadjustment.get_lower() == 0.0
    assert view.vadjustment.get_upper() == 0.0
    assert view.vadjustment.get_step_increment() == 0.0
    assert view.vadjustment.get_page_increment() == 0.0
    assert view.vadjustment.get_page_size() == 0.0


def test_scroll_adjustments(view, scrolled_window):
    assert scrolled_window.get_hadjustment() is view.hadjustment
    assert scrolled_window.get_vadjustment() is view.vadjustment


def test_will_not_remove_lone_controller(view):
    ctrl = Gtk.EventControllerMotion.new()

    removed = view.remove_controller(ctrl)

    assert not removed


def test_can_add_and_remove_controller(view):
    ctrl = Gtk.EventControllerMotion.new()
    view.add_controller(ctrl)

    removed = view.remove_controller(ctrl)

    assert removed
    assert ctrl not in view.observe_controllers()


def test_can_remove_all_controllers(view):
    ctrl = Gtk.EventControllerMotion.new()
    view.add_controller(ctrl)

    view.remove_all_controllers()

    assert ctrl not in view.observe_controllers()
