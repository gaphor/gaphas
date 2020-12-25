from gi.repository import Gtk

from gaphas.tool.scroll import on_scroll, scroll_tool


def test_scroll_tool_returns_a_controller(view):
    tool = scroll_tool(view)

    assert isinstance(tool, Gtk.EventController)


def test_offset_changes(view):
    tool = scroll_tool(view)

    on_scroll(tool, 10, 10, 1)

    assert view.matrix()[4] == -10
    assert view.matrix()[5] == -10
