from gi.repository import Gtk

from gaphas.tool.pan import on_scroll, pan_tool


def test_pan_tool_returns_a_controller(view):
    tool = pan_tool(view)

    assert isinstance(tool, Gtk.EventController)


def test_offset_changes(view):

    on_scroll(None, 10, 10, 1, view)

    assert view.matrix[4] == -10
    assert view.matrix[5] == -10
