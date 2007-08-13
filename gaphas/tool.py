"""
Tools are used to add interactive behavior to a View.

Tools can either not act on an event (None), just handle the event
or grab the event and all successive events until the tool is done
(e.g. on a button press/release).

The tools in this module are made to work properly in a ToolChain.

Current tools:
    ToolChain - for chaining individual tools together.
    HoverTool - make the item under the mouse cursor the "hovered item"
    ItemTool - handle selection and movement of items
    HandleTool - handle selection and movement of handles
    RubberbandTool - for Rubber band selection
    PlacementTool - for placing items on the canvas

Maybe even:
    TextEditTool - for editing text on canvas items (that support it)
    
    (context.view = view; context.grab() to grab, context.ungrab() to ungrab)
"""

__version__ = "$Revision$"
# $HeadURL$

import cairo
import gtk
from canvas import Context
from item import Element
from geometry import Rectangle

DEBUG_TOOL = False
DEBUG_TOOL_CHAIN = False


class ToolContext(Context):
    """
    Special context for tools.
    """

    view = None

    def __init__(self, **kwargs):
        super(ToolContext, self).__init__(**kwargs)

    def grab(self):
        """
        Grab the view (or tool, depending on the implementation).
        """
        self.view.grab_focus()

    def ungrab(self):
        """
        Ungrab the view.
        """
        pass


class Tool(object):

    def __init__(self):
        pass

    def on_button_press(self, context, event):
        """
        Mouse (pointer) button click. A button press is normally followed by
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
        """
        Button release event, that follows on a button press event.
        Not that double and tripple clicks'...
        """
        if DEBUG_TOOL: print 'on_button_release', context, event
        pass

    def on_double_click(self, context, event):
        """
        Event emited when the user does a double click (click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_double_click', context, event
        pass

    def on_triple_click(self, context, event):
        """
        Event emited when the user does a triple click (click-click-click)
        on the View.
        """
        if DEBUG_TOOL: print 'on_triple_click', context, event
        pass

    def on_motion_notify(self, context, event):
        """
        Mouse (pointer) is moved.
        """
        if DEBUG_TOOL: print 'on_motion_notify', context, event
        pass

    def on_key_press(self, context, event):
        """
        Keyboard key is pressed.
        """
        if DEBUG_TOOL: print 'on_key_press', context, event
        pass

    def on_key_release(self, context, event):
        """
        Keyboard key is released again (follows a key press normally).
        """
        if DEBUG_TOOL: print 'on_key_release', context, event
        pass

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


class ToolChainContext(Context):
    """
    ToolChainContext is a wrapper for the ToolContext.
    In addition to normal grab/ungrab behavior, it selects the tool that
    is requesting the grab() as the one tool that will receive subsequent
    requests until it is ungrab()'ed.
    """

    def __init__(self, tool_chain, tool_context, **kwargs):
        super(ToolChainContext, self).__init__(**kwargs)
        self.__dict__['_tool_chain'] = tool_chain
        self.__dict__['_tool_context'] = tool_context

    def __getattr__(self, key):
        """
        Delegate the getattr request to the wrapped tool_context.
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
    """
    A ToolChain can be used to chain tools together, for example HoverTool,
    HandleTool, SelectionTool.

    The grabbed item is bypassed in case a double or tripple click event
    is received. Should make sure this doesn't end up in dangling states.
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
        """
        Handle the event by calling each tool until the event is handled
        or grabbed.
        """
        context = ToolChainContext(tool_chain=self, tool_context=context)
        if self._grabbed_tool and event.type not in (gtk.gdk._2BUTTON_PRESS, gtk.gdk._3BUTTON_PRESS):
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

    def draw(self, context):
        if self._grabbed_tool:
            self._grabbed_tool.draw(context)


class HoverTool(Tool):
    """
    Make the item under the mouse cursor the "hovered item".
    """
    
    def __init__(self):
        pass

    def on_motion_notify(self, context, event):
        view = context.view
        old_hovered = view.hovered_item
        view.hovered_item = view.get_item_at_point(event.x, event.y)
        return None


class ItemTool(Tool):
    """
    ItemTool does selection and dragging of items. On a button click,
    the currently "hovered item" is selected. If CTRL or SHIFT are pressed,
    already selected items remain selected. The last selected item gets the
    focus (e.g. receives key press events).
    """
    
    def __init__(self, buttons=(1,)):
        self.last_x = 0
        self.last_y = 0
        self._buttons = buttons
        self._movable_items = set()

    def on_button_press(self, context, event):
        view = context.view
        if event.button not in self._buttons:
            return False
        self.last_x, self.last_y = event.x, event.y
        # Deselect all items unless CTRL or SHIFT is pressed
        # or the item is already selected.
        if not (event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
                or view.hovered_item in view.selected_items):
            del view.selected_items
        if view.hovered_item:
            if view.hovered_item in view.selected_items and \
               event.state & gtk.gdk.CONTROL_MASK:
                view.focused_item = None
                view.unselect_item(view.hovered_item)
            else:
                view.focused_item = view.hovered_item
                context.grab()

                # Filter the items that should eventually be moved
                get_ancestors = view.canvas.get_ancestors
                selected_items = set(view.selected_items)
                for i in selected_items:
                    # Do not move subitems of selected items
                    if not set(get_ancestors(i)).intersection(selected_items):
                        self._movable_items.add(i)

            return True

    def on_button_release(self, context, event):
        if event.button not in self._buttons:
            return False
        self._movable_items.clear()
        context.ungrab()
        return True

    def on_motion_notify(self, context, event):
        """
        Normally do nothing.
        If a button is pressed move the items around.
        """
        if event.state & gtk.gdk.BUTTON_PRESS_MASK:
            # Move selected items
            view = context.view
            canvas = view.canvas

            # Calculate the distance the item has to be moved
            dx, dy = event.x - self.last_x, event.y - self.last_y

            # Now do the actual moving.
            for i in self._movable_items:
                # Move the item and schedule it for an update
                v2i = view.get_matrix_v2i(i)
                i.matrix.translate(*v2i.transform_distance(dx, dy))
                canvas.request_matrix_update(i)

            self.last_x, self.last_y = event.x, event.y
            return True


class HandleTool(Tool):
    """
    Tool for moving handles around. By default this tool does not provide
    connecting handles to another item (see examples.ConnectingHandleTool for
    an example).
    """

    def __init__(self):
        self._grabbed_handle = None
        self._grabbed_item = None

    def grab_handle(self, item, handle):
        """
        Grab a specific handle. This can be used from the PlacementTool
        (and unittests) to set the state of the handle tool.
        """
        assert item is None and handle is None or handle in item.handles()
        self._grabbed_item = item
        self._grabbed_handle = handle


    def _find_handle(self, view, event, item):
        """
        Find item's handle at (event.x, event.y)
        """
        i2v = view.get_matrix_i2v(item).transform_point
        x, y = event.x, event.y
        for h in item.handles():
            if not h.movable:
                continue
            wx, wy = i2v(h.x, h.y)
            if -6 < (wx - x) < 6 and -6 < (wy - y) < 6:
                return h
        return None


    def find_handle(self, view, event):
        """
        Look for a handle at (event.x, event.y) and return the
        tuple (item, handle).
        """
        # The focused item is the prefered item for handle grabbing
        if view.focused_item:
            h = self._find_handle(view, event, view.focused_item)
            if h:
                return view.focused_item, h

        # then try hovered item
        if view.hovered_item:
            h = self._find_handle(view, event, view.hovered_item)
            if h:
                return view.hovered_item, h

        # Last try all items, checking the bounding box first
        x, y = event.x, event.y
        items = view.get_items_in_rectangle((x - 6, y - 6, 12, 12), reverse=True)
        
        found_item, found_h = None, None
        for item in items:
            h = self._find_handle(view, event, item)
            if h:
                return item, h
        return None, None


    def move(self, view, item, handle, x, y):
        """
        Move the handle to position ``(x,y)``. ``x`` and ``y`` are in
        item coordnates.
        """
        handle.x = x
        handle.y = y


    def glue(self, view, item, handle, vx, vy):
        """
        Find an item near ``handle` that ``item`` can connect to.
        ``vx`` and ``vy`` are the pointer (view) coordinates.
        """

    def connect(self, view, item, handle, vx, vy):
        """
        Find an item near ``handle`` that ``item`` can connect to and connect.
        ``vx`` and ``vy`` are the pointer (view) coordinates.
        """

    def disconnect(self, view, item, handle):
        """
        Disconnect the handle. This mostly comes down to removing 
        constraints.
        """

    def on_button_press(self, context, event):
        """
        Handle button press events. If the (mouse) button is pressed on
        top of a Handle (item.Handle), that handle is grabbed and can be
        dragged around.
        """
        view = context.view
        item, handle = self.find_handle(view, event)
        if handle:
            # Deselect all items unless CTRL or SHIFT is pressed
            # or the item is already selected.
            if not (event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)
                    or view.hovered_item in view.selected_items):
                del view.selected_items
            view.hovered_item = item
            view.focused_item = item
            self.grab_handle(item, handle)

            context.grab()
            if handle.connectable:
                self.disconnect(view, item, handle)

            return True

    def on_button_release(self, context, event):
        """
        Release a grabbed handle.
        """
        # queue extra redraw to make sure the item is drawn properly
        try:
            view = context.view
            if self._grabbed_handle and self._grabbed_handle.connectable:
                self.connect(view, self._grabbed_item, self._grabbed_handle, event.x, event.y)
        finally:
            context.ungrab()
        if self._grabbed_handle:
            self._grabbed_item.request_update()
        return True

    def on_motion_notify(self, context, event):
        """
        Handle motion events. If a handle is grabbed: drag it around,
        else, if the pointer is over a handle, make the owning item the
        hovered-item.
        """
        view = context.view
        if self._grabbed_handle and event.state & gtk.gdk.BUTTON_PRESS_MASK:
            canvas = view.canvas
            item = self._grabbed_item
            handle = self._grabbed_handle

            v2i = view.get_matrix_v2i(item)
            x, y = v2i.transform_point(event.x, event.y)

            # Do the actual move:
            self.move(view, item, handle, x, y)
            
            # do not request matrix update as matrix recalculation will be
            # performed due to item normalization if required
            item.request_update(matrix=False)
            try:
                if self._grabbed_handle.connectable:
                    self.glue(view, item, handle, event.x, event.y)
            finally:
                pass
            return True
        else:
            # Make the item who's handle we hover over the hovered_item:
            item, handle = self.find_handle(view, event)
            if item:
                view.hovered_item = item
                return True


class RubberbandTool(Tool):

    def __init__(self):
        self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

    def on_button_press(self, context, event):
        context.grab()
        self.x0, self.y0 = event.x, event.y
        self.x1, self.y1 = event.x, event.y
        return True

    def on_button_release(self, context, event):
        context.ungrab()
        self.queue_draw(context.view)
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        context.view.select_in_rectangle((min(x0, x1), min(y0, y1),
                 abs(x1 - x0), abs(y1 - y0)))
        return True

    def on_motion_notify(self, context, event):
        if event.state & gtk.gdk.BUTTON_PRESS_MASK:
            view = context.view
            self.queue_draw(view)
            self.x1, self.y1 = event.x, event.y
            self.queue_draw(view)
            return True

    def queue_draw(self, view):
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        view.queue_draw_area(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))

    def draw(self, context):
        cr = context.cairo
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        cr.set_line_width(1.0)
        cr.set_source_rgba(.5, .5, .7, .6)
        cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        cr.fill()


class PlacementTool(Tool):

    def __init__(self, factory, handle_tool, handle_index):
        self._factory = factory
        self._handle_tool = handle_tool
        self._handle_index = handle_index
        self._new_item = None

    handle_tool = property(lambda s: s._handle_tool, doc="Handle tool")
    handle_index = property(lambda s: s._handle_index,
                            doc="Index of handle to be used by handle_tool")
    new_item = property(lambda s: s._new_item, doc="The newly created item")

    def on_button_press(self, context, event):
        view = context.view
        canvas = view.canvas
        new_item = self._create_item(context, event.x, event.y)
        self._handle_tool.grab_handle(new_item,
                                      new_item.handles()[self._handle_index])
        self._new_item = new_item
        view.focused_item = new_item
        context.grab()
        return True

    def _create_item(self, context, x, y):
        view = context.view
        canvas = view.canvas
        item = self._factory()
        x, y = view.get_matrix_v2i(item).transform_point(x, y)
        item.matrix.translate(x, y)
        return item

    def on_button_release(self, context, event):
        context.ungrab()
        if self._new_item:
            h = self._handle_tool._grabbed_handle
            self._handle_tool.on_button_release(context, event)
        self._new_item = None
        return True

    def on_motion_notify(self, context, event):
        if self._new_item:
            return self._handle_tool.on_motion_notify(context, event)
        else:
            return False


class TextEditTool(Tool):
    """
    Demo of a text edit tool (just displays a text edit box at the cursor
    position.
    """

    def __init__(self):
        pass

    def on_double_click(self, context, event):
        """
        Create a popup window with some editable text.
        """
        window = gtk.Window()
        window.set_property('decorated', False)
        window.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        #window.set_modal(True)
        window.set_parent_window(context.view.window)
        buffer = gtk.TextBuffer()
        text_view = gtk.TextView()
        text_view.set_buffer(buffer)
        text_view.show()
        window.add(text_view)
        window.size_allocate(gtk.gdk.Rectangle(int(event.x), int(event.y), 50, 50))
        #window.move(int(event.x), int(event.y))
        cursor_pos = context.view.get_toplevel().get_screen().get_display().get_pointer()
        window.move(cursor_pos[1], cursor_pos[2])
        window.connect('focus-out-event', self._on_focus_out_event, buffer)
        text_view.connect('key-press-event', self._on_key_press_event, buffer)
        #text_view.set_size_request(50, 50)
        window.show()
        #text_view.grab_focus()
        #window.set_uposition(event.x, event.y)
        #window.focus
        return True

    def _on_key_press_event(self, widget, event, buffer):
        if event.keyval == gtk.keysyms.Return:
            print 'Enter!'
            #widget.get_toplevel().destroy()
        elif event.keyval == gtk.keysyms.Escape:
            print 'Escape!'
            widget.get_toplevel().destroy()

    def _on_focus_out_event(self, widget, event, buffer):
        print 'focus out!', buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        widget.destroy()


def DefaultTool():
    """
    The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
    chain = ToolChain()
    chain.append(HoverTool())
    chain.append(HandleTool())
    chain.append(ItemTool())
    chain.append(TextEditTool())
    chain.append(RubberbandTool())
    return chain


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
