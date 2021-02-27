import pytest
from gi.repository import Gtk

from gaphas.item import Element
from gaphas.tool.placement import PlacementState, on_drag_begin, placement_tool


@pytest.fixture
def tool_factory(connections):
    def tool_factory():
        return Element(connections)

    return tool_factory


def test_can_create_placement_tool(view, tool_factory):
    tool = placement_tool(view, tool_factory, 2)

    assert isinstance(tool, Gtk.Gesture)


def test_create_new_element(view, tool_factory, window):
    state = PlacementState(tool_factory, 2)
    tool = placement_tool(view, tool_factory, 2)
    view.add_controller(tool)

    on_drag_begin(tool, 0, 0, state)

    assert state.moving
