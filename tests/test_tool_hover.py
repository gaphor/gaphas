import pytest

from gaphas.tool.hover import hover_tool, on_motion
from gaphas.tool.itemtool import default_find_item_and_handle_at_point


@pytest.mark.asyncio
async def test_hovers_item(view, box):
    tool = hover_tool()
    view.add_controller(tool)

    on_motion(tool, 5, 5, default_find_item_and_handle_at_point)

    assert view.selection.hovered_item is box


def test_handles_event(view, box):
    tool = hover_tool()
    view.add_controller(tool)

    on_motion(tool, 100, 100, default_find_item_and_handle_at_point)

    assert view.selection.hovered_item is None
