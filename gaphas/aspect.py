"""Defines aspects for Items.

Aspects form intermediate items between tools and items.
"""
from functools import singledispatch

from gi.repository import Gdk

from gaphas.connections import Connections
from gaphas.item import Element, matrix_i2i


class ItemFinder:
    """Find an item on the canvas."""

    def __init__(self, view):
        """
        Initialize the view

        Args:
            self: (todo): write your description
            view: (bool): write your description
        """
        self.view = view

    def get_item_at_point(self, pos):
        """
        Return the item at the given position

        Args:
            self: (todo): write your description
            pos: (str): write your description
        """
        item, handle = self.view.get_handle_at_point(pos)
        return item or self.view.get_item_at_point(pos)


Finder = singledispatch(ItemFinder)


class ItemSelection:
    """A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @aspect decorator to a
    subclass.
    """

    def __init__(self, item, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.view = view

    def select(self):
        """Set selection on the view."""
        self.view.selection.set_focused_item(self.item)

    def unselect(self):
        """
        Unselects the given selection.

        Args:
            self: (todo): write your description
        """
        self.view.selection.set_focused_item(None)
        self.view.selection.unselect_item(self.item)


Selection = singledispatch(ItemSelection)


class ItemInMotion:
    """Aspect for dealing with motion on an item.

    In this case the item is moved.
    """

    def __init__(self, item, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, pos):
        """
        Move the cursor.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        self.last_x, self.last_y = pos

    def move(self, pos):
        """Move the item.

        x and y are in view coordinates.
        """
        item = self.item
        view = self.view
        v2i = view.get_matrix_v2i(item)

        x, y = pos
        dx, dy = x - self.last_x, y - self.last_y
        dx, dy = v2i.transform_distance(dx, dy)
        self.last_x, self.last_y = x, y

        item.matrix.translate(dx, dy)
        view.canvas.request_matrix_update(item)

    def stop_move(self):
        """
        Stop the move.

        Args:
            self: (todo): write your description
        """
        pass


InMotion = singledispatch(ItemInMotion)


class ItemHandleFinder:
    """Deals with the task of finding handles."""

    def __init__(self, item, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos):
        """
        Get the handle at pos

        Args:
            self: (todo): write your description
            pos: (str): write your description
        """
        return self.view.get_handle_at_point(pos)


HandleFinder = singledispatch(ItemHandleFinder)


class ItemHandleSelection:
    """Deal with selection of the handle."""

    def __init__(self, item, handle, view):
        """
        Add a new item.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            handle: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.handle = handle
        self.view = view

    def select(self):
        """
        Selects the next item.

        Args:
            self: (todo): write your description
        """
        pass

    def unselect(self):
        """
        Unselect the next item.

        Args:
            self: (todo): write your description
        """
        pass


HandleSelection = singledispatch(ItemHandleSelection)


@HandleSelection.register(Element)
class ElementHandleSelection(ItemHandleSelection):
    CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")

    def select(self):
        """
        Selects the currently selected window.

        Args:
            self: (todo): write your description
        """
        index = self.item.handles().index(self.handle)
        if index < 4:
            display = self.view.get_display()
            cursor = Gdk.Cursor.new_from_name(display, self.CURSORS[index])
            self.view.get_window().set_cursor(cursor)

    def unselect(self):
        """
        Unselect a : class : class.

        Args:
            self: (todo): write your description
        """
        from .view import DEFAULT_CURSOR

        cursor = Gdk.Cursor(DEFAULT_CURSOR)
        self.view.get_window().set_cursor(cursor)


class ItemHandleInMotion:
    """Move a handle (role is applied to the handle)"""

    GLUE_DISTANCE = 10

    def __init__(self, item, handle, view):
        """
        Initialize the item.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            handle: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.handle = handle
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, pos):
        """
        Start a new canvas

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        self.last_x, self.last_y = pos
        canvas = self.view.canvas

        cinfo = canvas.connections.get_connection(self.handle)
        if cinfo:
            canvas.solver.remove_constraint(cinfo.constraint)

    def move(self, pos):
        """
        Translates the item.

        Args:
            self: (todo): write your description
            pos: (int): write your description
        """
        item = self.item
        view = self.view

        v2i = view.get_matrix_v2i(item)

        x, y = v2i.transform_point(*pos)

        self.handle.pos = (x, y)

        sink = self.glue(pos)

        # do not request matrix update as matrix recalculation will be
        # performed due to item normalization if required
        view.canvas.request_update(item, matrix=False)

        return sink

    def stop_move(self):
        """
        Stop the move.

        Args:
            self: (todo): write your description
        """
        pass

    def glue(self, pos, distance=GLUE_DISTANCE):
        """Glue to an item near a specific point.

        Returns a ConnectionSink or None.
        """
        item = self.item
        handle = self.handle
        view = self.view

        if not handle.connectable:
            return None

        connectable, port, glue_pos = view.get_port_at_point(
            pos, distance=distance, exclude=(item,)
        )

        # check if item and found item can be connected on closest port
        if port is not None:
            assert connectable is not None

            connections = self.view.canvas.connections
            connector = Connector(self.item, self.handle, connections)
            sink = ConnectionSink(connectable, port)

            if connector.allow(sink):
                # transform coordinates from view space to the item
                # space and update position of item's handle
                v2i = view.get_matrix_v2i(item).transform_point
                handle.pos = v2i(*glue_pos)
                return sink
        return None


HandleInMotion = singledispatch(ItemHandleInMotion)


class ItemConnector:
    """Connect or disconnect an item's handle to another item or port."""

    GLUE_DISTANCE = 10  # Glue distance in view points

    def __init__(self, item, handle, connections: Connections):
        """
        Initialize the connection.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            handle: (todo): write your description
            connections: (todo): write your description
        """
        self.item = item
        self.handle = handle
        self.connections = connections

    def allow(self, sink):
        """
        Allow the given sink.

        Args:
            self: (todo): write your description
            sink: (todo): write your description
        """
        return True

    def glue(self, sink):
        """Glue the Connector handle on the sink's port."""
        handle = self.handle
        item = self.item
        matrix = matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        gluepos, dist = sink.port.glue(pos)
        matrix.invert()
        handle.pos = matrix.transform_point(*gluepos)

    def connect(self, sink):
        """Connect the handle to a sink (item, port).

        Note that connect() also takes care of disconnecting in case a
        handle is reattached to another element.
        """

        cinfo = self.connections.get_connection(self.handle)

        # Already connected? disconnect first.
        if cinfo:
            self.disconnect()

        if not self.allow(sink):
            return

        self.glue(sink)

        self.connect_handle(sink)

    def connect_handle(self, sink, callback=None):
        """Create constraint between handle of a line and port of connectable
        item.

        :Parameters:
         sink
            Connectable item and port.
         callback
            Function to be called on disconnection.
        """
        handle = self.handle
        item = self.item

        constraint = sink.port.constraint(item, handle, sink.item)

        self.connections.connect_item(
            item, handle, sink.item, sink.port, constraint, callback=callback
        )

    def disconnect(self):
        """Disconnect the handle from the attached element."""
        self.connections.disconnect_item(self.item, self.handle)


Connector = singledispatch(ItemConnector)


class ItemConnectionSink:
    """Makes an item a sink.

    A sink is another item that an item's handle is connected to like a
    connectable item or port.
    """

    def __init__(self, item, port):
        """
        Initialize a new port.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            port: (int): write your description
        """
        self.item = item
        self.port = port

    def find_port(self, pos):
        """Glue to the closest item on the canvas.

        If the item can connect, it returns a port.
        """
        port = None
        max_dist = 10e6
        for p in self.item.ports():
            pg, d = p.glue(pos)
            if d >= max_dist:
                continue
            port = p
            max_dist = d

        return port


ConnectionSink = singledispatch(ItemConnectionSink)


#
# Painter aspects
#


class ItemPaintFocused:
    """Paints on top of all items, just for the focused item and only when it's
    hovered (see gaphas.painter.FocusedItemPainter)"""

    def __init__(self, item, view):
        """
        Initialize the view.

        Args:
            self: (todo): write your description
            item: (todo): write your description
            view: (bool): write your description
        """
        self.item = item
        self.view = view

    def paint(self, cairo):
        """
        Paint a set of the given cairo.

        Args:
            self: (todo): write your description
            cairo: (todo): write your description
        """
        pass


PaintFocused = singledispatch(ItemPaintFocused)
