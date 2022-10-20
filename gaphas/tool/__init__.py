"""Tools provide interactive behavior to a `View` by handling specific events
sent by view.

Some of implemented tools are

`HoverTool`
    make the item under the mouse cursor the "hovered item"

`ItemTool`
    handle selection and movement of items

`HandleTool`
    handle selection and movement of handles

`RubberbandTool`
    for rubber band selection of multiple items

`PanTool`
    for easily moving the canvas around

`PlacementTool`
    for placing items on the canvas

The tools are chained with `ToolChain` class (it is a tool as well),
which allows to combine functionality provided by different tools.

Tools can handle events in different ways

- event can be ignored
- tool can handle the event (obviously)
"""
from gaphas.tool.hover import hover_tool
from gaphas.tool.itemtool import item_tool
from gaphas.tool.placement import placement_tool
from gaphas.tool.rubberband import rubberband_tool
from gaphas.tool.scroll import scroll_tool, scroll_tools
from gaphas.tool.viewfocus import view_focus_tool
from gaphas.tool.zoom import zoom_tool, zoom_tools
