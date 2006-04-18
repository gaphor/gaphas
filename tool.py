"""Tools are used to add interactive behavior to a View.

Tools can either not act on an event (None), just handle the event
or grab the event and all successive events until the tool is done
(e.g. on a button press/release).

The tools in this module are made to work properly in a ToolChain.

Current tools:
    ToolChain - for chaining individual tools together.
    HoverTool - make the item under the mouse cursor the "hovered item"
    ItemTool - handle selection and movement of items
    HandleTool - handle selection and movement of handles

Required:
    PlacementTool - for placing items on the canvas
    RubberBandTool - for Rubber band selection

Maybe even:
    TextEditTool - for editing text on canvas items (that support it)
    
    (context.view = view; context.grab() to grab, context.ungrab() to ungrab)
"""

import cairo
import gtk
from canvas import Context

DEBUG_TOOL = False
DEBUG_TOOL_CHAIN = False

class Tool(object):

    def __init__(self):
        pass

    def on_button_press(self, context, event):
        """Mouse (pointer) button click. A button press is normally followed by
        a button release. Double and triple clicks should work together with
        the button methods.

        A single click is emited as:
                on_button_press
                on_button_release

        In case of a double click:
                single click +
                on_button_press
                on_double_click
                on_button_release

        In case of a tripple click:
                double click +
                on_button_press
                on_triple_click
                on_button_release
        """
        if DEBUG_TOOL: print 'on_button_press', context, event

    def on_button_release(self, context, event):
        """Button release event, that follows on a button press event.
        Not that double and tripple clicks'...
        """
        if DEBUG_TOOL: print 'on_button_release', context, event
        pass

    def on_double_click(self, context, event):
        """Event emited when the user does a double click (click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_double_click', context, event
        pass

    def on_triple_click(self, context, event):
        """Event emited when the user does a triple click (click-click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_triple_click', context, event
        pass

    def on_motion_notify(self, context, event):
        """Mouse (pointer) is moved.
        """
        if DEBUG_TOOL: print 'on_motion_notify', context, event
        pass

    def on_key_press(self, context, event):
        """Keyboard key is pressed.
        """
        if DEBUG_TOOL: print 'on_key_press', context, event
        pass

    def on_key_release(self, context, event):
        """Keyboard key is released again (follows a key press normally).
        """
        if DEBUG_TOOL: print 'on_key_release', context, event
        pass

    def draw(self, context):
        """Some tools (such as Rubberband selection) may need to draw something
        on the canvas. This can be done through the draw() method. This is
        called after all items are drawn.
        The context contains the following fields:
         - context: the render context (contains context.view and context.cairo)
         - cairo: the Cairo drawing context
        """
        pass
        
class ToolChainContext(Context):
    """ToolChainContext is a wrapper for the view.ToolContext.
    In addition to normal grab/ungrab behavior, it selects the tool that
    is requesting the grab() as the one tool that will receive subsequent
    requests until it is ungrab()'ed.
    """

    def __init__(self, tool_chain, tool_context, **kwargs):
        super(ToolChainContext, self).__init__(**kwargs)
        self.__dict__['_tool_chain'] = tool_chain
        self.__dict__['_tool_context'] = tool_context

    def __getattr__(self, key):
        """Delegate the getattr request to the wrapped tool_context.
        """
        return getattr(self._tool_context, key)

    def set_tool(self, tool):
        self.__dict__['_tool'] = tool

    def grab(self):
        self._tool_context.grab()
        self._tool_chain.grab(self._tool)

    def ungrab(self):
        self._tool_context.ungrab()
        self._tool_chain.ungrab(self._tool)


class ToolChain(Tool):
    """A ToolChain can be used to chain tools together, for example HoverTool,
    HandleTool, SelectionTool.
    """

    def __init__(self):
        self._tools = []
        self._grabbed_tool = None

    def append(self, tool):
        self._tools.append(tool)

    def prepend(self, tool):
        self._tools.insert(0, tool)

    def grab(self, tool):
        if not self._grabbed_tool:
            if DEBUG_TOOL_CHAIN: print 'Grab tool', tool
            self._grabbed_tool = tool

    def ungrab(self, tool):
        if self._grabbed_tool is tool:
            if DEBUG_TOOL_CHAIN: print 'UNgrab tool', self._grabbed_tool
            self._grabbed_tool = None

    def _handle(self, func, context, event):
        """Handle the event by calling each tool until the event is handled
        or grabbed.
        """
        context = ToolChainContext(tool_chain=self, tool_context=context)
        if self._grabbed_tool:
            context.set_tool(self._grabbed_tool)
            return getattr(self._grabbed_tool, func)(context, event)
        else:
            for tool in self._tools:
                if DEBUG_TOOL_CHAIN: print 'tool', tool
                context.set_tool(tool)
                rt = getattr(tool, func)(context, event)
                if rt:
                    return rt
        
    def on_button_press(self, context, event):
        self._handle('on_button_press', context, event)

    def on_button_release(self, context, event):
        self._handle('on_button_release', context, event)

    def on_double_click(self, context, event):
        self._handle('on_double_click', context, event)

    def on_triple_click(self, context, event):
        self._handle('on_triple_click', context, event)

    def on_motion_notify(self, context, event):
        self._handle('on_motion_notify', context, event)

    def on_key_press(self, context, event):
        self._handle('on_key_press', context, event)

    def on_key_release(self, context, event):
        self._handle('on_key_release', context, event)


class HoverTool(Tool):
    """Make the item under the mouse cursor the "hovered item".
    """
    
    def __init__(self):
        pass

    def on_motion_notify(self, context, event):
        view = context.view
        old_hovered = view.hovered_item
        view.hovered_item = view.get_item_at_point(event.x, event.y)
        return None


class ItemTool(Tool):
    """ItemTool does selection and dragging of items. On a button click,
    the currently "hovered item" is selected. If CTRL or SHIFT are pressed,
    already selected items remain selected. The last selected item gets the
    focus (e.g. receives key press events).
    """

    def __init__(self):
        self.last_x = 0
        self.last_y = 0

    def on_button_press(self, context, event):
        view = context.view
        self.last_x, self.last_y = event.x, event.y
        # Deselect all items unless CTRL or SHIFT is pressed
        # or the item is already selected.
        if not (event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
                or view.hovered_item in view.selected_items):
            del view.selected_items
        if view.hovered_item:
            view.focused_item = view.hovered_item
        context.grab()
        return True

    def on_button_release(self, context, event):
        context.ungrab()
        return True

    def on_motion_notify(self, context, event):
        """Normally, just check which item is under the mouse pointer
        and make it the view.hovered_item.
        """
        if event.state & gtk.gdk.BUTTON_PRESS_MASK:
            view = context.view
            # Move selected items

            # First request redraws for all items, before enything is
            # changed.
            for i in view.selected_items:
                # Set a redraw request before the item is updated
                view.queue_draw_item(i, handles=True)

            # Now do the actual moving.
            for i in view.selected_items:
                # Do not move subitems of selected items
                anc = set(view.canvas.get_ancestors(i))
                if anc.intersection(view.selected_items):
                    continue

                # Calculate the distance the item has to be moved
                dx, dy = view.transform_distance_c2w(event.x - self.last_x, event.y - self.last_y)
                # Move the item and schedule it for an update
                i.matrix.translate(*view.canvas.get_matrix_w2i(i).transform_distance(dx, dy))
                i.request_update()
                i.canvas.update_matrices()
                b = i._view_bounds
                view.queue_draw_item(i, handles=True)
                view.queue_draw_area(b[0] + dx-1, b[1] + dy-1, b[2] - b[0]+2, b[3] - b[1]+2)
            self.last_x, self.last_y = event.x, event.y
        return True


class HandleTool(Tool):

    def __init__(self):
        self._grabbed_handle = None
        self._grabbed_item = None

    def on_button_press(self, context, event):
        view = context.view
        self._grabbed_handle = None
        self._grabbed_item = None
        itemlist = view.canvas.get_all_items()
        # The focused item is the prefered item for handle grabbing
        if view.focused_item:
            # We can savely do this, since the list is a copy of the list
            # maintained by the canvas
            itemlist.append(view.focused_item)

        wx, wy = view.transform_point_c2w(event.x, event.y)

        for item in reversed(itemlist):
            x, y = view.canvas.get_matrix_w2i(item).transform_point(wx, wy)
            for h in item.handles():
                if abs(x - h.x) < 5 and abs(y - h.y) < 5:
                    self._grabbed_handle = h
                    self._grabbed_item = item
                    self.last_x, self.last_y = event.x, event.y
                    # Deselect all items unless CTRL or SHIFT is pressed
                    # or the item is already selected.
                    if not (event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
                            or view.hovered_item in view.selected_items):
                        del view.selected_items
                    view.hovered_item = item
                    view.focused_item = item
                    context.grab()
                    return True

    def on_button_release(self, context, event):
        context.ungrab()
        return True

    def on_motion_notify(self, context, event):
        if self._grabbed_handle and event.state & gtk.gdk.BUTTON_PRESS_MASK:
            view = context.view
            # Calculate the distance the item has to be moved
            dx, dy = view.transform_distance_c2w(event.x - self.last_x, event.y - self.last_y)
            item = self._grabbed_item
            handle = self._grabbed_handle

            view.queue_draw_item(item, handles=True)

            # Move the item and schedule it for an update
            dx, dy = view.canvas.get_matrix_w2i(item).transform_distance(dx, dy)
            handle.x += dx
            handle.y += dy
            
            item.request_update()
            item.canvas.update_matrices()

            view.queue_draw_item(item, handles=True)
            self.last_x, self.last_y = event.x, event.y
            return True


def DefaultToolChain():
    """The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
    chain = ToolChain()
    chain.append(HoverTool())
    chain.append(HandleTool())
    chain.append(ItemTool())
    return chain


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
