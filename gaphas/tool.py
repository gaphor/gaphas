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
- event and all successive events can be grabbed until the tool is done
  (e.g. on a button press/release), see `Context.grab` and `Context.ungrab`
  methods
"""

__version__ = "$Revision$"
# $HeadURL$

import sys

import cairo
import gtk
from gaphas.canvas import Context
from gaphas.geometry import Rectangle
from gaphas.geometry import distance_point_point_fast, distance_line_point
from gaphas.item import Line

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

    def on_scroll(self, context, event):
        """
        Scroll wheel was turned.
        """
        if DEBUG_TOOL: print 'on_scroll', context, event, event.direction
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
        """
        Append a tool to the chain. Self is returned.
        """
        self._tools.append(tool)
        return self

    def prepend(self, tool):
        """
        Prepend a tool to the chain. Self is returned.
        """
        self._tools.insert(0, tool)
        return self

    def swap(self, old_tool_class, new_tool):
        """
        Swap one tool for another. Note that the first argument is the tool's
        class (type), not an instance.

        >>> chain = ToolChain().append(HoverTool()).append(RubberbandTool())
        >>> chain._tools # doctest: +ELLIPSIS
        [<gaphas.tool.HoverTool object at 0x...>, <gaphas.tool.RubberbandTool object at 0x...>]
        >>> chain.swap(HoverTool, ItemTool()) # doctest: +ELLIPSIS
        <gaphas.tool.ToolChain object at 0x...>

        Now the HoverTool has been substituted for the ItemTool:
        
        >>> chain._tools # doctest: +ELLIPSIS
        [<gaphas.tool.ItemTool object at 0x...>, <gaphas.tool.RubberbandTool object at 0x...>]
        """
        tools = self._tools
        for i in xrange(len(tools)):
            if type(tools[i]) is old_tool_class:
                if self._grabbed_tool is tools[i]:
                    raise ValueError, 'Can\'t swap tools since %s is grabbed' % tools[i]
                tools[i] = new_tool
                break
        return self

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

    def on_scroll(self, context, event):
        self._handle('on_scroll', context, event)

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
        view.hovered_item = view.get_item_at_point((event.x, event.y))
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

            # TODO: if isinstance(item, Element):
            #   schedule item to be handled by some "guides" tool
            #   that tries to align the handle with some other Element's
            #   handle.

            self.last_x, self.last_y = event.x, event.y
            return True


class HandleTool(Tool):
    """
    Tool for moving handles around. By default this tool does not provide
    connecting handles to another item (see `ConnectHandleTool`).
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

    def ungrab_handle(self):
        """
        Reset _grabbed_handle and _grabbed_item.
        """
        self._grabbed_handle = None
        self._grabbed_item = None

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


    def move(self, view, item, handle, pos):
        """
        Move the handle to position ``(x,y)``. ``x`` and ``y`` are in
        item coordnates. ``item`` is the item whose ``handle`` is moved.
        """
        handle.x, handle.y = pos


    def glue(self, view, item, handle, vpos):
        """
        Find an item that ``handle`` can connect to. ``item`` is the ``Item``
        owing the handle.
        ``vpos`` is the point in the pointer (view) coordinates.

        The ``glue()`` code should take care of moving ``handle`` to the
        correct position, creating a glue effect.
        """

    def connect(self, view, item, handle, vpos):
        """
        Find an item that ``handle`` can connect to and create a connection.
        ``item`` is the ``Item`` owning the handle.
        ``vpos`` is the point in the pointer (view) coordinates.
        
        A typical connect action may involve the following:
        
        - Find an item near ``handle`` that can be connected to.
        - Move ``handle`` to the right position.
        - Set ``handle.connected_to`` to point to the new item.
        - Add constraints to the constraint solver (``view.canvas.solver``).
        - Set ``handle.disconnect`` to point to a method that can be called when
          the handle is disconnected (no arguments).
        
        NOTE: ``connect()`` can not expect ``glue()`` has been called,
        therefore it should ensure the handle is moved to the correct location
        before.
        """

    def disconnect(self, view, item, handle):
        """
        Disconnect the handle. This mostly comes down to removing 
        constraints. ``item`` is the Item owning the handle.

        A typical disconnect operation may look like this:
        
        - Call ``handle.disconnect()`` (assigned in ``connect()``).
        - Disconnect existing constraints.
        - Set ``handle.connected_to`` to ``None``.
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
        grabbed_handle, grabbed_item = self._grabbed_handle, self._grabbed_item
        try:
            view = context.view
            if grabbed_handle and grabbed_handle.connectable:
                self.connect(view, grabbed_item, grabbed_handle, (event.x, event.y))
        finally:
            context.ungrab()
            self.ungrab_handle()

        if grabbed_handle:
            grabbed_item.request_update()
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
            self.move(view, item, handle, (x, y))
            
            # do not request matrix update as matrix recalculation will be
            # performed due to item normalization if required
            item.request_update(matrix=False)
            try:
                if self._grabbed_handle.connectable:
                    self.glue(view, item, handle, (event.x, event.y))
                # TODO: elif isinstance(item, Element):
                #   schedule (item, handle) to be handled by some "guides" tool
                #   that tries to align the handle with some other Element's
                #   handle.
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


class PanTool(Tool):
    """
    Captures drag events with the middle mouse button and uses them to
    translate the canvas within the view. Trumps the ZoomTool, so should be
    placed later in the ToolChain.
    """

    def __init__(self):
        self.x0, self.y0 = 0, 0
        self.speed = 10

    def on_button_press(self,context,event):
        if event.button == 2:
            context.grab()
            self.x0, self.y0 = event.x, event.y
            return True

    def on_button_release(self, context, event):
        context.ungrab()
        self.x0, self.y0 = event.x, event.y
        return True

    def on_motion_notify(self, context, event):
        if event.state & gtk.gdk.BUTTON2_MASK:
            view = context.view
            dx = self.x0 - event.x
            dy = self.y0 - event.y
            if dx:
                adj = context.view.hadjustment
                adj.value = adj.value + dx
                adj.value_changed()
                self.x0 = event.x

            if dy:
                adj = context.view.vadjustment
                adj.value = adj.value + dy
                adj.value_changed()
                self.y0 = event.y
            return True

    def on_scroll(self, context, event):
        direction = event.direction
        gdk = gtk.gdk
        adj = None
        if direction == gdk.SCROLL_LEFT:
            adj = context.view.hadjustment
            adj.value = adj.value - self.speed
        elif direction == gdk.SCROLL_RIGHT:
            adj = context.view.hadjustment
            adj.value = adj.value + self.speed
        elif direction == gdk.SCROLL_UP:
            adj = context.view.vadjustment
            adj.value = adj.value - self.speed
        elif direction == gdk.SCROLL_DOWN:
            adj = context.view.vadjustment
            adj.value = adj.value + self.speed
        if adj:
            adj.value_changed()
        return True


class PlacementTool(Tool):

    def __init__(self, factory, handle_tool, handle_index):
        self._factory = factory
        self._handle_tool = handle_tool
        self._handle_index = handle_index
        self._new_item = None
        self._grabbed_handle = None

    handle_tool = property(lambda s: s._handle_tool, doc="Handle tool")
    handle_index = property(lambda s: s._handle_index,
                            doc="Index of handle to be used by handle_tool")
    new_item = property(lambda s: s._new_item, doc="The newly created item")


    def on_button_press(self, context, event):
        view = context.view
        canvas = view.canvas
        new_item = self._create_item(context, (event.x, event.y))
        # Enforce matrix update, as a good matrix is required for the handle
        # positioning:
        canvas.get_matrix_i2c(new_item, calculate=True)

        self._new_item = new_item
        view.focused_item = new_item

        h = new_item.handles()[self._handle_index]
        if h.movable:
            self._handle_tool.grab_handle(new_item, h)
            self._grabbed_handle = h
            context.grab()
        return True


    def _create_item(self, context, pos):
        view = context.view
        canvas = view.canvas
        item = self._factory()
        x, y = view.get_matrix_v2i(item).transform_point(*pos)
        item.matrix.translate(x, y)
        return item


    def on_button_release(self, context, event):
        context.ungrab()
        if self._grabbed_handle:
            self._handle_tool.on_button_release(context, event)
            self._grabbed_handle = None
        self._new_item = None
        return True

    def on_motion_notify(self, context, event):
        if self._grabbed_handle:
            return self._handle_tool.on_motion_notify(context, event)
        else:
            # act as if the event is handled if we have a new item
            return bool(self._new_item)


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



class ConnectHandleTool(HandleTool):
    """
    Tool for connecting two items.
    
    There are two items involved. Handle of connecting item (usually
    a line) is being dragged by an user towards another item (item in
    short). Port of an item is found by the tool and connection is
    established by creating a constraint between line's handle and item's
    port.
    """
    # distance between line and item
    GLUE_DISTANCE = 10

    def glue(self, view, line, handle, vpos):
        """
        Find an item for connection with a line.

        Method looks for items in glue rectangle (which is defined by
        ``vpos`` (vx, vy) and glue distance), then finds the closest port.

        Glue position for closest port is calculated as well. Handle of
        a line is moved to glue point to indicate that connection is about
        to happen.

        Found item and its connection port are returned. If item is not
        found nor suitable port, then tuple `(None, None)` is returned.

        :Parameters:
         view
            View used by user.
         line
            Connecting item.
         handle
            Handle of line (connecting item).
        """
        if not handle.connectable:
            return None

        dist = self.GLUE_DISTANCE
        max_dist = dist
        port = None
        glue_pos = None
        item = None
        v2i = view.get_matrix_v2i
        vx, vy = vpos

        rect = (vx - dist, vy - dist, dist * 2, dist * 2)
        items = view.get_items_in_rectangle(rect, reverse=True)
        for i in items:
            if i is line:
                continue
            for p in i.ports():
                if not p.connectable:
                    continue

                ix, iy = v2i(i).transform_point(vx, vy)
                pg, d = p.glue((ix, iy))

                if d >= max_dist:
                    continue

                item = i
                port = p

                # transform coordinates from connectable item space to view
                # space
                i2v = view.get_matrix_i2v(i).transform_point
                glue_pos = i2v(*pg)

        # check if line and found item can be connected on closest port
        if port is not None \
                and not self.can_glue(view, line, handle, item, port):
            item, port = None, None

        if port is not None:
            # transform coordinates from view space to the line space and
            # update position of line's handle
            v2i = view.get_matrix_v2i(line).transform_point
            handle.pos = v2i(*glue_pos)

        return item, port


    def can_glue(self, view, line, handle, item, port):
        """
        Determine if line's handle can connect to a port of an item.

        `True` is returned by default. Override this method to disallow
        glueing in higher level of application stack (i.e. when classes of
        line and item does not match).

        :Parameters:
         view
            View used by user.
         line
            Item connecting to connectable item.
         handle
            Handle of line connecting to connectable item.
         item
            Connectable item.
         port
            Port of connectable item.
        """
        return True


    def pre_connect(self, view, line, handle, item, port):
        """
        The method is invoked just before connection is performed by
        `ConnectHandleTool.connect` method. It can be overriden by deriving
        tools to perform connection in higher level of application stack.

        `True` is returned to indicate that higher level connection is
        performed.

        :Parameters:
         view
            View used by user.
         line
            Item connecting to connectable item.
         handle
            Handle of line connecting to connectable item.
         item
            Connectable item.
         port
            Port of connectable item.
        """
        return True


    def connect(self, view, line, handle, vpos):
        """
        Connect a handle of a line to connectable item.

        Connectable item is found by `ConnectHandleTool.glue` method.

        Return `True` if connection is performed.

        :Parameters:
         view
            View used by user.
         line
            Connecting item.
         handle
            Handle of connecting item.
        """
        # find connectable item and its port
        item, port = self.glue(view, line, handle, vpos)

        # disconnect when
        # - no connectable item
        # - currently connected item is not connectable item
        if not item \
                or item and handle.connected_to is not item:
            handle.disconnect()

        # no connectable item, no connection
        if not item:
            return

        # connection in higher level of application stack
        self.pre_connect(view, line, handle, item, port)
        # low-level connection
        self.post_connect(view.canvas, line, handle, item, port)


    def post_connect(self, canvas, line, handle, item, port):
        """
        Create constraint between handle of a line and port of connectable
        item.

        :Parameters:
         canvas
            Canvas owning the items.
         line
            Connecting item.
         handle
            Handle of connecting item.
         item
            Connectable item.
         port
            Port of connectable item.
        """
        ConnectHandleTool.create_constraint(line, handle, item, port)

        handle.connected_to = item
        handle.disconnect = DisconnectHandle(canvas, line, handle)


    def disconnect(self, view, line, handle):
        """
        Disconnect line (connecting item) from an item.

        :Parameters:
         view
            View used by user.
         line
            Connecting item.
         handle
            Handle of connecting item.
        """
        if handle.disconnect:
            handle.disconnect()


    @staticmethod
    def find_port(line, handle, item):
        """
        Find port of an item at position of line's handle.

        :Parameters:
         line
            Line supposed to connect to an item.
         handle
            Handle of a line connecting to an item.
         item
            Item to be connected to a line.
        """
        port = None
        max_dist = sys.maxint
        canvas = item.canvas

        # line's handle position to canvas coordinates
        i2c = canvas.get_matrix_i2c(line)
        hx, hy = i2c.transform_point(*handle.pos)

        # from canvas to item coordinates
        c2i = canvas.get_matrix_c2i(item)
        ix, iy = c2i.transform_point(hx, hy)

        # find the port using item's coordinates
        for p in item.ports():
            pg, d = p.glue((ix, iy))
            if d >= max_dist:
                continue
            port = p
            max_dist = d

        return port


    @staticmethod
    def create_constraint(line, handle, item, port):
        """
        Create connection constraint between line's handle and item's port.

        If constraint already exists, then it is removed and new constraint
        is created instead.

        :Parameters:
         line
            Line connecting to an item.
         handle
            Handle of a line connecting to an item.
         item
            Item to be connected to a line.
         port
            Item's port used for connection with a line.
        """
        canvas = line.canvas
        solver = canvas.solver

        if handle.connection_data:
            solver.remove_constraint(handle.connection_data)

        constraint = port.constraint(canvas, line, handle, item)
        handle.connection_data = constraint
        solver.add_constraint(constraint)


    @staticmethod
    def remove_constraint(line, handle):
        """
        Remove connection constraint created between line's handle and
        connected item's port.

        :Parameters:
         line
            Line connecting to an item.
         handle
            Handle of a line connecting to an item.
        """
        if handle.connection_data:
            line.canvas.solver.remove_constraint(handle.connection_data)
            handle.connection_data = None



class DisconnectHandle(object):

    def __init__(self, canvas, item, handle):
        self.canvas = canvas
        self.item = item
        self.handle = handle

    def __call__(self):
        self.handle_disconnect()

    def handle_disconnect(self):
        canvas = self.canvas
        item = self.item
        handle = self.handle
        try:
            canvas.solver.remove_constraint(handle.connection_data)
        except KeyError:
            print 'constraint was already removed for', item, handle
            pass # constraint was alreasy removed
        else:
            print 'constraint removed for', item, handle
        handle.connection_data = None
        handle.connected_to = None
        # Remove disconnect handler:
        handle.disconnect = None


class LineSegmentTool(ConnectHandleTool):
    """
    Line segment tool provides functionality for splitting and merging line
    segments.

    Line segment is defined by two adjacent handles.

    Line splitting is performed by clicking a line in the middle of
    a segment.

    Line merging is performed by moving a handle onto adjacent handle.

    Please note, that this tool provides functionality without involving
    context menu. Any further research into line spliting/merging
    functionality should take into account this assumption and new
    improvements (or even this tool replacement) shall be behavior based.

    It is possible to use this tool from a menu by using
    `LineSegmentTool.split_segment` and `LineSegmentTool.merge_segment`
    methods.
    """
    def split_segment(self, line, segment, count=2):
        """
        Split one line segment into ``count`` equal pieces.

        Two lists are returned
        
        - list of created handles
        - list of created ports

        :Parameters:
         line
            Line item, which segment shall be split.
         segment
            Segment number to split (starting from zero).
         count
            Amount of new segments to be created (minimum 2). 
        """
        if segment < 0 or segment >= len(line.ports()):
            raise ValueError('Incorrect segment')
        if count < 2:
            raise ValueError('Incorrect count of segments')

        def do_split(segment, count):
            handles = line.handles()
            h0 = handles[segment]
            h1 = handles[segment + 1]
            dx, dy = h1.x - h0.x, h1.y - h0.y
            new_h = line._create_handle((h0.x + dx / count, h0.y + dy / count))
            line._reversible_insert_handle(segment + 1, new_h)

            p0 = line._create_port(h0, new_h)
            p1 = line._create_port(new_h, h1)
            line._reversible_remove_port(line.ports()[segment])
            line._reversible_insert_port(segment, p0)
            line._reversible_insert_port(segment + 1, p1)

            if count > 2:
                do_split(segment + 1, count - 1)

        # get rid of connection constraints (to be recreated later)
        citems, chandles = self._remove_constraints(line)

        do_split(segment, count)

        # force orthogonal constraints to be recreated
        line._update_orthogonal_constraints(line.orthogonal)

        # recreate connection constraints
        self._recreate_constraints(citems, chandles, line)

        handles = line.handles()[segment + 1:segment + count]
        ports = line.ports()[segment:segment + count - 1]
        return handles, ports


    def merge_segment(self, line, segment, count=2):
        """
        Merge two (or more) line segments.

        Tuple of two lists is returned, list of deleted handles and list of
        deleted ports.

        :Parameters:
         line
            Line item, which segments shall be merged.
         segment
            Segment number to start merging from (starting from zero).
         count
            Amount of segments to be merged (minimum 2). 
        """
        if len(line.ports()) < 2:
            raise ValueError('Cannot merge line with one segment')
        if segment < 0 or segment >= len(line.ports()):
            raise ValueError('Incorrect segment')
        if count < 2 or segment + count > len(line.ports()):
            raise ValueError('Incorrect count of segments')

        # get rid of connection constraints (to be recreated later)
        citems, chandles = self._remove_constraints(line)

        # remove handle and ports which share position with handle
        deleted_handles = line.handles()[segment + 1:segment + count]
        deleted_ports = line.ports()[segment:segment + count]
        for h in deleted_handles:
            line._reversible_remove_handle(h)
        for p in deleted_ports:
            line._reversible_remove_port(p)

        # create new port, which replaces old ports destroyed due to
        # deleted handle
        h1 = line.handles()[segment]
        h2 = line.handles()[segment + 1]
        port = line._create_port(h1, h2)
        line._reversible_insert_port(segment, port)

        # force orthogonal constraints to be recreated
        line._update_orthogonal_constraints(line.orthogonal)

        # recreate connection constraints
        self._recreate_constraints(citems, chandles, line)

        return deleted_handles, deleted_ports


    def _recreate_constraints(self, lines, handles, item):
        """
        Create connection constraints between connecting lines and an item.

        :Parameters:
         lines
            Lines connecting to an item.
         handles
            Handles connecting to an item.
         item
            Item connected to lines.
        """
        for line, h in zip(lines, handles):
            port = ConnectHandleTool.find_port(line, h, item)
            ConnectHandleTool.create_constraint(line, h, item, port)


    def _remove_constraints(self, item):
        """
        Remove connection constraints established between an item and all
        connecting items.

        List of connecting items and list of connecting handles are
        returned.

        :Parameters:
         item
            Item, to which connections shall be removed.
        """
        lines = []
        handles = []
        if item.canvas: # no canvas, no connections
            data = item.canvas.get_connected_items(item)
            for line, h in data:
                ConnectHandleTool.remove_constraint(line, h)
            if data:
                lines, handles = zip(*data)

        return lines, handles


    def on_button_press(self, context, event):
        """
        In addition to the normal behaviour, the button press event creates
        new handles if it is activated on the middle of a line segment.
        """
        if super(LineSegmentTool, self).on_button_press(context, event):
            return True

        view = context.view
        item = view.hovered_item
        if item and item is view.focused_item and isinstance(item, Line):
            handles = item.handles()
            x, y = view.get_matrix_v2i(item).transform_point(event.x, event.y)
            for h1, h2 in zip(handles[:-1], handles[1:]):
                xp = (h1.x + h2.x) / 2
                yp = (h1.y + h2.y) / 2
                if distance_point_point_fast((x,y), (xp, yp)) <= 4:
                    segment = handles.index(h1)
                    self.split_segment(item, segment)

                    self.grab_handle(item, item.handles()[segment + 1])
                    context.grab()
                    return True


    def on_button_release(self, context, event):
        """
        In addition to the normal behavior, the button release event
        removes line segment if grabbed handle is close enough to an
        adjacent handle.
        """
        grabbed_handle = self._grabbed_handle
        grabbed_item = self._grabbed_item
        if super(LineSegmentTool, self).on_button_release(context, event):
            if grabbed_handle and grabbed_item:
                handles = grabbed_item.handles()

                # don't merge using first or last handle
                if handles[0] is grabbed_handle or handles[-1] is grabbed_handle:
                    return True

                handle_index = handles.index(grabbed_handle)
                segment = handle_index - 1

                # cannot merge starting from last segment
                if segment == len(grabbed_item.ports()) - 1:
                    segment =- 1
                assert segment >= 0 and segment < len(grabbed_item.ports()) - 1

                before = handles[handle_index - 1]
                after = handles[handle_index + 1]
                d, p = distance_line_point(before.pos, after.pos, grabbed_handle.pos)

                if d < 2:
                    assert len(context.view.canvas.solver._marked_cons) == 0
                    self.merge_segment(grabbed_item, segment)

            return True



def DefaultTool():
    """
    The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
        #append(ConnectHandleTool()). \
    chain = ToolChain(). \
        append(HoverTool()). \
        append(LineSegmentTool()). \
        append(PanTool()). \
        append(ItemTool()). \
        append(TextEditTool()). \
        append(RubberbandTool())
    return chain


# vim: sw=4:et:ai
