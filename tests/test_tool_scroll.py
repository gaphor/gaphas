from gi.repository import Gtk

from gaphas.tool.scroll import on_scroll, scroll_tool


def test_scroll_tool_returns_a_controller(view):
    tool = scroll_tool(view)

    assert isinstance(tool, Gtk.EventController)


def test_offset_changes(view, scrolled_window):
    tool = scroll_tool(view)
    view.add_controller(tool)
    view._scrolling.update_adjustments(100, 100, (0, 0, 100, 100))

    assert view.hadjustment
    assert view.vadjustment
    assert view._scrolling._hadjustment_handler_id
    assert view._scrolling._hadjustment_handler_id

    on_scroll(tool, 10, 10, 1)

    assert view.matrix[4] == -10
    # Why is this value not set?
    assert view.matrix[5] == 0
