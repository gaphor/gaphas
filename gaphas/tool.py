#!/usr/bin/env python

# Copyright (C) 2006-2017 Adrian Boguszewski <adrbogus1@student.pg.gda.pl>
#                         Arjan Molenaar <gaphor@gmail.com>
#                         Artur Wroblewski <wrobell@pld-linux.org>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.

"""
Tools provide interactive behavior to a `View` by handling specific events
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

The tools are chained with `ToolChain` class (it is a tool as well), which
allows to combine functionality provided by different tools.

Tools can handle events in different ways

- event can be ignored
- tool can handle the event (obviously)
"""

import toga

from gaphas.aspect import (Finder, Selection, InMotion,
    HandleFinder, HandleSelection, HandleInMotion,
    Connector)
from gaphas.itemcontainer import Context

DEBUG_TOOL_CHAIN = False

Event = Context


class Tool(object):
    """
    Base class for a tool. This class 
    A word on click events:

    Mouse (pointer) button click. A button press is normally followed by
    a button release. Double and triple clicks should work together with
    the button methods.

    A single click is emited as:
            on_button_press
            on_button_release

    In case of a double click:
            on_button_press (x 2)
            on_double_click
            on_button_release

    In case of a tripple click:
            on_button_press (x 3)
            on_triple_click
            on_button_release
    """

    # Custom events:
    GRAB = -100
    UNGRAB = -101

    # Map events to tool methods
    EVENT_HANDLERS = {
        # Custom events:
        GRAB: 'on_grab',
        UNGRAB: 'on_ungrab',
    }

    # Those events force the tool to release the grabbed tool.
    # FORCE_UNGRAB_EVENTS = (Gdk.EventType._2BUTTON_PRESS, Gdk.EventType._3BUTTON_PRESS)

    def __init__(self, view=None):
        self.view = view

    def set_view(self, view):
        self.view = view

    def _dispatch(self, event):
        """
        Deal with the event. The event is dispatched to a specific handler
        for the event type.
        """
        handler = self.EVENT_HANDLERS.get(event.type)
        if handler:
            try:
                h = getattr(self, handler)
            except AttributeError:
                pass  # No handler
            else:
                return bool(h(event))
        return False

    def handle(self, event):
        return self._dispatch(event)

    def draw(self, context):
        """
        Some tools (such as Rubberband selection) may need to draw something
        on the canvas. This can be done through the draw() method. This is
        called after all items are drawn.
        The context contains the following fields:

        - context: the render context (contains context.view and context.cairo)
        - cairo: the Cairo drawing context
        """
        pass


class ToolChain(Tool):
    """
    A ToolChain can be used to chain tools together, for example HoverTool,
    HandleTool, SelectionTool.

    The grabbed item is bypassed in case a double or tripple click event
    is received. Should make sure this doesn't end up in dangling states.
    """

    def __init__(self, view=None):
        super(ToolChain, self).__init__(view)
        self._tools = []
        self._grabbed_tool = None

    def set_view(self, view):
        self.view = view
        for tool in self._tools:
            tool.set_view(self.view)

    def append(self, tool):
        """
        Append a tool to the chain. Self is returned.
        """
        self._tools.append(tool)
        tool.view = self.view
        return self

    def grab(self, tool):
        if not self._grabbed_tool:
            if DEBUG_TOOL_CHAIN:
                print('Grab tool', tool)
            # Send grab event
            event = Event(type=Tool.GRAB)
            tool.handle(event)
            self._grabbed_tool = tool

    def ungrab(self, tool):
        if self._grabbed_tool is tool:
            if DEBUG_TOOL_CHAIN:
                print('UNgrab tool', self._grabbed_tool)
            # Send ungrab event
            event = Event(type=Tool.UNGRAB)
            tool.handle(event)
            self._grabbed_tool = None

    def validate_grabbed_tool(self, event):
        """
        Check if it's valid to have a grabbed tool on an event. If not the
        grabbed tool will be released.
        """
        if event.type in self.FORCE_UNGRAB_EVENTS:
            self.ungrab(self._grabbed_tool)

    # def handle(self, event):
    #     """
    #     Handle the event by calling each tool until the event is handled
    #     or grabbed.
    #
    #     If a tool is returning True on a button press event, the motion and
    #     button release events are also passed to this
    #     """
    #     handler = self.EVENT_HANDLERS.get(event.type)
    #
    #     self.validate_grabbed_tool(event)
    #
    #     if self._grabbed_tool and handler:
    #         try:
    #             return self._grabbed_tool.handle(event)
    #         finally:
    #             if event.type == Gdk.EventType.BUTTON_RELEASE:
    #                 self.ungrab(self._grabbed_tool)
    #     else:
    #         for tool in self._tools:
    #             if DEBUG_TOOL_CHAIN:
    #                 print('tool', tool)
    #             rt = tool.handle(event)
    #             if rt:
    #                 if event.type == Gdk.EventType.BUTTON_PRESS:
    #                     self.view.grab_focus()
    #                     self.grab(tool)
    #                 return rt

    def draw(self, context):
        if self._grabbed_tool:
            self._grabbed_tool.draw(context)


class HoverTool(Tool):
    """
    Make the item under the mouse cursor the "hovered item".
    """

    def on_motion_notify(self, event):
        view = self.view
        pos = event.x, event.y
        view.hovered_item = Finder(view).get_item_at_point(pos)


class ItemTool(Tool):
    """
    ItemTool does selection and dragging of items. On a button click,
    the currently "hovered item" is selected. If CTRL or SHIFT are pressed,
    already selected items remain selected. The last selected item gets the
    focus (e.g. receives key press events).

    The roles used are Selection (select, unselect) and InMotion (move).
    """

    def __init__(self, view=None, buttons=(1,)):
        super(ItemTool, self).__init__(view)
        self._buttons = buttons
        self._movable_items = set()

    def get_item(self):
        return self.view.hovered_item

    def movable_items(self):
        """
        Filter the items that should eventually be moved.

        Returns InMotion aspects for the items.
        """
        view = self.view
        get_ancestors = view.canvas.get_ancestors
        selected_items = set(view.selected_items)
        for item in selected_items:
            # Do not move subitems of selected items
            if not set(get_ancestors(item)).intersection(selected_items):
                yield InMotion(item, view)

    def on_button_press(self, event):
        # TODO: make keys configurable
        view = self.view
        item = self.get_item()

        if event.get_button()[1] not in self._buttons:
            return False

        # Deselect all items unless CTRL or SHIFT is pressed
        # or the item is already selected.
        # if not (event.get_state()[1] & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
        #         or item in view.selected_items):
        #     del view.selected_items
        #
        # if item:
        #     if view.hovered_item in view.selected_items and \
        #                     event.get_state()[1] & Gdk.ModifierType.CONTROL_MASK:
        #         selection = Selection(item, view)
        #         selection.unselect()
        #     else:
        #         selection = Selection(item, view)
        #         selection.select()
        #         self._movable_items.clear()
        #     return True

    def on_button_release(self, event):
        if event.get_button()[1] not in self._buttons:
            return False
        for inmotion in self._movable_items:
            inmotion.stop_move()
        self._movable_items.clear()
        return True

    # def on_motion_notify(self, event):
    #     """
    #     Normally do nothing.
    #     If a button is pressed move the items around.
    #     """
    #     if event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK:
    #
    #         if not self._movable_items:
    #             self._movable_items = set(self.movable_items())
    #             for inmotion in self._movable_items:
    #                 inmotion.start_move((event.x, event.y))
    #
    #         for inmotion in self._movable_items:
    #             inmotion.move((event.x, event.y))
    #
    #         return True


class HandleTool(Tool):
    """
    Tool for moving handles around.

    By default this tool does not provide connecting handles to another item
    (see `ConnectHandleTool`).
    """

    def __init__(self, view=None):
        super(HandleTool, self).__init__(view)
        self.grabbed_handle = None
        self.grabbed_item = None
        self.motion_handle = None

    def grab_handle(self, item, handle):
        """
        Grab a specific handle. This can be used from the PlacementTool
        to set the state of the handle tool.
        """
        assert item is None and handle is None or handle in item.handles()
        self.grabbed_item = item
        self.grabbed_handle = handle

        selection = HandleSelection(item, handle, self.view)
        selection.select()

    def ungrab_handle(self):
        """
        Reset grabbed_handle and grabbed_item.
        """
        item = self.grabbed_item
        handle = self.grabbed_handle
        self.grabbed_handle = None
        self.grabbed_item = None
        if handle:
            selection = HandleSelection(item, handle, self.view)
            selection.unselect()

    def on_button_press(self, event):
        """
        Handle button press events. If the (mouse) button is pressed on
        top of a Handle (item.Handle), that handle is grabbed and can be
        dragged around.
        """
        view = self.view

        item, handle = HandleFinder(view.hovered_item, view).get_handle_at_point((event.x, event.y))

        # if handle:
        #     # Deselect all items unless CTRL or SHIFT is pressed
        #     # or the item is already selected.
        #     # TODO: duplicate from ItemTool
        #     if not (event.get_state()[1] & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
        #             or view.hovered_item in view.selected_items):
        #         del view.selected_items
        #     #
        #     view.hovered_item = item
        #     view.focused_item = item
        #
        #     self.motion_handle = None
        #
        #     self.grab_handle(item, handle)
        #
        #     return True

    def on_button_release(self, event):
        """
        Release a grabbed handle.
        """
        # queue extra redraw to make sure the item is drawn properly
        grabbed_handle, grabbed_item = self.grabbed_handle, self.grabbed_item

        if self.motion_handle:
            self.motion_handle.stop_move()
            self.motion_handle = None

        self.ungrab_handle()

        if grabbed_handle:
            grabbed_item.request_update()
        return True

    def on_motion_notify(self, event):
        """
        Handle motion events. If a handle is grabbed: drag it around,
        else, if the pointer is over a handle, make the owning item the
        hovered-item.
        """
        view = self.view
        # if self.grabbed_handle and event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK:
        #     canvas = view.canvas
        #     item = self.grabbed_item
        #     handle = self.grabbed_handle
        #     pos = event.x, event.y
        #
        #     if not self.motion_handle:
        #         self.motion_handle = HandleInMotion(item, handle, self.view)
        #         self.motion_handle.start_move(pos)
        #     self.motion_handle.move(pos)
        #
        #     return True


class RubberbandTool(Tool):
    def __init__(self, view=None):
        super(RubberbandTool, self).__init__(view)
        self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

    def on_button_press(self, event):
        self.x0, self.y0 = event.x, event.y
        self.x1, self.y1 = event.x, event.y
        return True

    def on_button_release(self, event):
        self.queue_draw(self.view)
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        self.view.select_in_rectangle((min(x0, x1), min(y0, y1),
                                       abs(x1 - x0), abs(y1 - y0)))
        return True

    # def on_motion_notify(self, event):
    #     if event.get_state()[1] & Gdk.EventMask.BUTTON_PRESS_MASK:
    #         view = self.view
    #         self.queue_draw(view)
    #         self.x1, self.y1 = event.x, event.y
    #         self.queue_draw(view)
    #         return True

    def queue_draw(self, view):
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        view.queue_draw_area(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))

    def draw(self, context):
        cr = context.cairo
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        cr.set_line_width(1.0)
        cr.set_source_rgba(.5, .5, .7, .5)
        cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        cr.fill()

#
# PAN_MASK = Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.CONTROL_MASK
# PAN_VALUE = 0


class PanTool(Tool):
    """
    Captures drag events with the middle mouse button and uses them to
    translate the canvas within the view. Trumps the ZoomTool, so should be
    placed later in the ToolChain.
    """

    def __init__(self, view=None):
        super(PanTool, self).__init__(view)
        self.x0, self.y0 = 0, 0
        self.speed = 10

    # def on_button_press(self, event):
    #     if not event.get_state()[1] & PAN_MASK == PAN_VALUE:
    #         return False
    #     if event.get_button()[1] == 2:
    #         self.x0, self.y0 = event.x, event.y
    #         return True

    def on_button_release(self, event):
        self.x0, self.y0 = event.x, event.y
        return True

    # def on_motion_notify(self, event):
    #     if event.get_state()[1] & Gdk.EventMask.BUTTON2_MOTION_MASK:
    #         view = self.view
    #         self.x1, self.y1 = event.x, event.y
    #         dx = self.x1 - self.x0
    #         dy = self.y1 - self.y0
    #         view._matrix.translate(dx / view._matrix[0], dy / view._matrix[3])
    #         # Make sure everything's updated
    #         view.request_update((), view._canvas.get_all_items())
    #         self.x0 = self.x1
    #         self.y0 = self.y1
    #         return True

#     def on_scroll(self, event):
#         # Ensure no modifiers
#         if not event.get_state()[1] & PAN_MASK == PAN_VALUE:
#             return False
#         view = self.view
#         direction = event.scroll.direction
#         if direction == Gdk.ScrollDirection.LEFT:
#             view._matrix.translate(self.speed / view._matrix[0], 0)
#         elif direction == Gdk.ScrollDirection.RIGHT:
#             view._matrix.translate(-self.speed / view._matrix[0], 0)
#         elif direction == Gdk.ScrollDirection.UP:
#             view._matrix.translate(0, self.speed / view._matrix[3])
#         elif direction == Gdk.ScrollDirection.DOWN:
#             view._matrix.translate(0, -self.speed / view._matrix[3])
#         view.request_update((), view._canvas.get_all_items())
#         return True
#
#
# ZOOM_MASK = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.MOD1_MASK
# ZOOM_VALUE = Gdk.ModifierType.CONTROL_MASK


class ZoomTool(Tool):
    """
    Tool for zooming using either of two techniques:

    - ctrl + middle-mouse dragging in the up-down direction.
    - ctrl + mouse-wheeel
    """

    def __init__(self, view=None):
        super(ZoomTool, self).__init__(view)
        self.x0, self.y0 = 0, 0
        self.lastdiff = 0;

    # def on_button_press(self, event):
    #     if event.get_button()[1] == 2 \
    #             and event.get_state()[1] & ZOOM_MASK == ZOOM_VALUE:
    #         self.x0 = event.x
    #         self.y0 = event.y
    #         self.lastdiff = 0
    #         return True

    def on_button_release(self, event):
        self.lastdiff = 0
        return True

    # def on_motion_notify(self, event):
    #     if event.get_state()[1] & ZOOM_MASK == ZOOM_VALUE \
    #             and event.get_state()[1] & Gdk.EventMask.BUTTON2_MOTION_MASK:
    #         view = self.view
    #         dy = event.y - self.y0
    #
    #         sx = view._matrix[0]
    #         sy = view._matrix[3]
    #         ox = (view._matrix[4] - self.x0) / sx
    #         oy = (view._matrix[5] - self.y0) / sy
    #
    #         if abs(dy - self.lastdiff) > 20:
    #             if dy - self.lastdiff < 0:
    #                 factor = 1. / 0.9
    #             else:
    #                 factor = 0.9
    #
    #             m = view.matrix
    #             m.translate(-ox, -oy)
    #             m.scale(factor, factor)
    #             m.translate(+ox, +oy)
    #
    #             # Make sure everything's updated
    #             view.request_update((), view._canvas.get_all_items())
    #
    #             self.lastdiff = dy
    #         return True

    # def on_scroll(self, event):
    #     if event.get_state()[1] & Gdk.ModifierType.CONTROL_MASK:
    #         view = self.view
    #         sx = view._matrix[0]
    #         sy = view._matrix[3]
    #         ox = (view._matrix[4] - event.scroll.x) / sx
    #         oy = (view._matrix[5] - event.scroll.y) / sy
    #         factor = 0.9
    #         if event.scroll.direction == Gdk.ScrollDirection.UP:
    #             factor = 1. / factor
    #         view._matrix.translate(-ox, -oy)
    #         view._matrix.scale(factor, factor)
    #         view._matrix.translate(+ox, +oy)
    #         # Make sure everything's updated
    #         view.request_update((), view._canvas.get_all_items())
    #         return True


class PlacementTool(Tool):
    def __init__(self, view, factory, handle_tool, handle_index):
        super(PlacementTool, self).__init__(view)
        self._factory = factory
        self.handle_tool = handle_tool
        handle_tool.set_view(view)
        self._handle_index = handle_index
        self._new_item = None
        self.grabbed_handle = None

    handle_index = property(lambda s: s._handle_index,
                            doc="Index of handle to be used by handle_tool")
    new_item = property(lambda s: s._new_item, doc="The newly created item")

    def on_button_press(self, event):
        view = self.view
        canvas = view.canvas
        new_item = self._create_item((event.x, event.y))
        # Enforce matrix update, as a good matrix is required for the handle
        # positioning:
        canvas.get_matrix_i2c(new_item, calculate=True)

        self._new_item = new_item
        view.focused_item = new_item

        h = new_item.handles()[self._handle_index]
        if h.movable:
            self.handle_tool.grab_handle(new_item, h)
            self.grabbed_handle = h
        return True

    def _create_item(self, pos, **kw):
        view = self.view
        item = self._factory(**kw)
        x, y = view.get_matrix_v2i(item).transform_point(*pos)
        item.matrix.translate(x, y)
        return item

    def on_button_release(self, event):
        if self.grabbed_handle:
            self.handle_tool.on_button_release(event)
            self.grabbed_handle = None
        self._new_item = None
        return True

    def on_motion_notify(self, event):
        if self.grabbed_handle:
            return self.handle_tool.on_motion_notify(event)
        else:
            # act as if the event is handled if we have a new item
            return bool(self._new_item)


class TextEditTool(Tool):
    """
    Demo of a text edit tool (just displays a text edit box at the cursor
    position.
    """

    def __init__(self, view=None):
        super(TextEditTool, self).__init__(view)

    def on_double_click(self, event):
        """
        Create a popup window with some editable text.
        """
        window = toga.Window(size=(50,50))
        # TODO how to support set_decorated is False
        # window.set_property('decorated', False)
        # TODO how to support set_parent_window?
        # window.set_parent_window(self.view.get_window())
        text_view = toga.TextInput()
        buffer = text_view.value()
        cursor_pos = self.view.get_toplevel().get_screen().get_display().get_pointer()
        window.move(cursor_pos[1], cursor_pos[2])
        window.connect('focus-out-event', self._on_focus_out_event, buffer)
        text_view.connect('key-press-event', self._on_key_press_event, buffer)
        window.show()
        return True

    # def _on_key_press_event(self, widget, event, buffer):
    #     if event.keyval == Gdk.KEY_Escape:
    #         widget.get_toplevel().destroy()

    def _on_focus_out_event(self, widget, event, buffer):
        widget.destroy()


class ConnectHandleTool(HandleTool):
    """
    Tool for connecting two items.

    There are two items involved. Handle of connecting item (usually
    a line) is being dragged by an user towards another item (item in
    short). Port of an item is found by the tool and connection is
    established by creating a constraint between line's handle and item's
    port.
    """

    def glue(self, item, handle, vpos):
        """
        Perform a small glue action to ensure the handle is at a proper
        location for connecting.
        """
        if self.motion_handle:
            return self.motion_handle.glue(vpos)
        else:
            return HandleInMotion(item, handle, self.view).glue(vpos)

    def connect(self, item, handle, vpos):
        """
        Connect a handle of a item to connectable item.

        Connectable item is found by `ConnectHandleTool.glue` method.

        :Parameters:
         item
            Connecting item.
         handle
            Handle of connecting item.
         vpos
            Position to connect to (or near at least)
        """
        connector = Connector(item, handle)

        # find connectable item and its port
        sink = self.glue(item, handle, vpos)

        # no new connectable item, then diconnect and exit
        if sink:
            connector.connect(sink)
        else:
            cinfo = item.canvas.get_connection(handle)
            if cinfo:
                connector.disconnect()

    def on_button_release(self, event):
        view = self.view
        item = self.grabbed_item
        handle = self.grabbed_handle
        try:
            if handle and handle.connectable:
                self.connect(item, handle, (event.x, event.y))
        finally:
            return super(ConnectHandleTool, self).on_button_release(event)


def DefaultTool(view=None):
    """
    The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
    return ToolChain(view). \
        append(HoverTool()). \
        append(ConnectHandleTool()). \
        append(PanTool()). \
        append(ZoomTool()). \
        append(ItemTool()). \
        append(TextEditTool()). \
        append(RubberbandTool())

# vim: sw=4:et:ai
