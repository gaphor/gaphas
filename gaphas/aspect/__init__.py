"""Defines aspects for Items.

Aspects form intermediate items between tools and items.
"""
from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING, Tuple, Union

from gi.repository import Gdk
from typing_extensions import Protocol

from gaphas.connections import Connections
from gaphas.connector import Handle, Port
from gaphas.item import Element, Item, matrix_i2i

if TYPE_CHECKING:
    from gaphas.view import GtkView, Selection

Pos = Tuple[float, float]


class ItemFinder:
    """Find an item on the canvas."""

    def __init__(self, view):
        self.view = view

    def get_item_at_point(self, pos: Pos):
        item, handle = self.view.get_handle_at_point(pos)
        return item or self.view.get_item_at_point(pos)


Finder = singledispatch(ItemFinder)


class ItemSelector:
    """A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @aspect decorator to a
    subclass.
    """

    def __init__(self, item: Item, selection: Selection):
        self.item = item
        self.selection = selection

    def select(self):
        """Set selection on the view."""
        self.selection.set_focused_item(self.item)

    def unselect(self):
        self.selection.set_focused_item(None)
        self.selection.unselect_item(self.item)


Selector = singledispatch(ItemSelector)


class ItemInMotion:
    """Aspect for dealing with motion on an item.

    In this case the item is moved.
    """

    last_x: float
    last_y: float

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def start_move(self, pos: Pos):
        self.last_x, self.last_y = pos

    def move(self, pos: Pos):
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
        pass


InMotion = singledispatch(ItemInMotion)


class ItemHandleFinder:
    """Deals with the task of finding handles."""

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos: Pos):
        return self.view.get_handle_at_point(pos)


HandleFinder = singledispatch(ItemHandleFinder)


class ItemHandleSelection:
    """Deal with selection of the handle."""

    def __init__(self, item: Item, handle: Handle, view: GtkView):
        self.item = item
        self.handle = handle
        self.view = view

    def select(self):
        pass

    def unselect(self):
        pass


HandleSelection = singledispatch(ItemHandleSelection)


@HandleSelection.register(Element)
class ElementHandleSelection(ItemHandleSelection):
    CURSORS = ("nw-resize", "ne-resize", "se-resize", "sw-resize")

    def select(self):
        index = self.item.handles().index(self.handle)
        if index < 4:
            display = self.view.get_display()
            cursor = Gdk.Cursor.new_from_name(display, self.CURSORS[index])
            self.view.get_window().set_cursor(cursor)

    def unselect(self):
        from .view import DEFAULT_CURSOR

        cursor = Gdk.Cursor(DEFAULT_CURSOR)
        self.view.get_window().set_cursor(cursor)


class ItemHandleInMotion:
    """Move a handle (role is applied to the handle)"""

    GLUE_DISTANCE = 10

    last_x: float
    last_y: float

    def __init__(self, item: Item, handle: Handle, view: GtkView):
        self.item = item
        self.handle = handle
        self.view = view

    def start_move(self, pos: Pos):
        self.last_x, self.last_y = pos
        canvas = self.view.canvas

        cinfo = canvas.connections.get_connection(self.handle)
        if cinfo:
            canvas.solver.remove_constraint(cinfo.constraint)

    def move(self, pos: Pos):
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
        pass

    def glue(self, pos: Pos, distance=GLUE_DISTANCE):
        """Glue to an item near a specific point.

        Returns a ConnectionSink or None.
        """
        item = self.item
        handle = self.handle
        view = self.view

        if not handle.connectable:
            return None

        connectable, port, glue_pos = get_port_at_point(
            view, pos, distance=distance, exclude=(item,)
        )

        # check if item and found item can be connected on closest port
        if connectable and port and glue_pos:
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


def get_port_at_point(
    view, vpos, distance=10, exclude=None
) -> Union[Tuple[Item, Port, Tuple[float, float]], Tuple[None, None, None]]:
    """Find item with port closest to specified position.

    List of items to be ignored can be specified with `exclude`
    parameter.

    Tuple is returned

    - found item
    - closest, connectable port
    - closest point on found port (in view coordinates)

    :Parameters:
        vpos
        Position specified in view coordinates.
        distance
        Max distance from point to a port (default 10)
        exclude
        Set of items to ignore.
    """
    v2i = view.get_matrix_v2i
    vx, vy = vpos

    max_dist = distance
    port = None
    glue_pos = None
    item = None

    rect = (vx - distance, vy - distance, distance * 2, distance * 2)
    for i in reversed(list(view.get_items_in_rectangle(rect))):
        if i in exclude:
            continue
        for p in i.ports():
            if not p.connectable:
                continue

            ix, iy = v2i(i).transform_point(vx, vy)
            pg, d = p.glue((ix, iy))

            if d >= max_dist:
                continue

            max_dist = d
            item = i
            port = p

            # transform coordinates from connectable item space to view
            # space
            i2v = view.get_matrix_i2v(i).transform_point
            glue_pos = i2v(*pg)
    return item, port, glue_pos  # type: ignore[return-value]


class ItemConnector:
    """Connect or disconnect an item's handle to another item or port."""

    GLUE_DISTANCE = 10  # Glue distance in view points

    def __init__(self, item: Item, handle: Handle, connections: Connections):
        self.item = item
        self.handle = handle
        self.connections = connections

    def allow(self, sink: ConnectionSinkType):
        return True

    def glue(self, sink: ConnectionSinkType):
        """Glue the Connector handle on the sink's port."""
        handle = self.handle
        item = self.item
        matrix = matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        gluepos, dist = sink.port.glue(pos)
        matrix.invert()
        handle.pos = matrix.transform_point(*gluepos)

    def connect(self, sink: ConnectionSinkType):
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

    def connect_handle(self, sink: ConnectionSinkType, callback=None):
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


class ConnectionSinkType(Protocol):
    item: Item
    port: Port

    def __init__(self, item: Item, port: Port):
        ...

    def find_port(self, pos):
        ...


class ItemConnectionSink:
    """Makes an item a sink.

    A sink is another item that an item's handle is connected to like a
    connectable item or port.
    """

    def __init__(self, item: Item, port: Port):
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

    def __init__(self, item: Item, view: GtkView):
        self.item = item
        self.view = view

    def paint(self, cairo):
        pass


PaintFocused = singledispatch(ItemPaintFocused)
