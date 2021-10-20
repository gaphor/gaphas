import pytest
from gi.repository import Gdk

from gaphas.tool.hover import hover_tool


@pytest.fixture
def motion_event():
    event = Gdk.Event()
    event.type = Gdk.EventType.MOTION_NOTIFY
    return event


def test_hovers_item(view, box, motion_event):
    tool = hover_tool(view)
    motion_event.x = 5
    motion_event.y = 5

    tool.handle_event(motion_event)

    assert view.selection.hovered_item is box


def test_handles_event(view, box, motion_event):
    tool = hover_tool(view)
    motion_event.x = 100
    motion_event.y = 100

    tool.handle_event(motion_event)

    assert view.selection.hovered_item is None
