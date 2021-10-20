import pytest
from gi.repository import Gdk, Gtk

from gaphas.tool.hover import hover_tool

GTK4 = Gtk._version == "4.0"


@pytest.fixture
def motion_event():
    event = Gdk.Event()
    event.type = Gdk.EventType.MOTION_NOTIFY
    return event


@pytest.mark.skipif(GTK4, reason="test does work on GTK 3 only")
def test_hovers_item(view, box, motion_event):
    tool = hover_tool(view)
    motion_event.x = 5
    motion_event.y = 5

    tool.handle_event(motion_event)

    assert view.selection.hovered_item is box


@pytest.mark.skipif(GTK4, reason="test does work on GTK 3 only")
def test_handles_event(view, box, motion_event):
    tool = hover_tool(view)
    motion_event.x = 100
    motion_event.y = 100

    tool.handle_event(motion_event)

    assert view.selection.hovered_item is None
