"""
Defines aspects for Items. Aspects form intermediate items between
tools and items.

Note: This module uses Phillip J. Eby's simplegeneric module. This
module transforms the generic class (used as fall-back) to a generic
function. In order to inherit from this class you should inherit from
Class.default.  The simplegeneric module is dispatching opnly based on
the first argument.  For Gaphas that's enough.
"""
from __future__ import absolute_import

from builtins import object

from gi.repository import Gdk
from simplegeneric import generic

from gaphas.item import Item, Element


class ItemFinder(object):
    """
    Find an item on the canvas.
    """

    def __init__(self, view):
        self.view = view

    def get_item_at_point(self, pos):
        item, handle = self.view.get_handle_at_point(pos)
        return item or self.view.get_item_at_point(pos)


Finder = generic(ItemFinder)


class ItemSelection(object):
    """
    A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @aspect decorator
    to a subclass.
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def select(self):
        """
        Set selection on the view.
        """
        self.view.focused_item = self.item

    def unselect(self):
        self.view.focused_item = None
        self.view.unselect_item(self.item)


Selection = generic(ItemSelection)


class ItemInMotion(object):
    """
    Aspect for dealing with motion on an item.

    In this case the item is moved.
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, pos):
        self.last_x, self.last_y = pos

    def move(self, pos):
        """
        Move the item. x and y are in view coordinates.
        """
        item = self.item
        view = self.view
        v2i = view.get_matrix_v2i(item)

        x, y = pos
        dx, dy = x - self.last_x, y - self.last_y
        dx, dy = v2i.transform_distance(dx, dy)
        self.last_x, self.last_y = x, y

        item.matrix.translate(dx, dy)
        item.canvas.request_matrix_update(item)

    def stop_move(self):
        pass


InMotion = generic(ItemInMotion)


class ItemHandleFinder(object):
    """
    Deals with the task of finding handles.
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos):
        return self.view.get_handle_at_point(pos)


HandleFinder = generic(ItemHandleFinder)


class ItemHandleSelection(object):
    """
    Deal with selection of the handle.
    """

    def __init__(self, item, handle, view):
        self.item = item
        self.handle = handle
        self.view = view

    def select(self):
        pass

    def unselect(self):
        pass


HandleSelection = generic(ItemHandleSelection)


@HandleSelection.when_type(Element)
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


class ItemHandleInMotion(object):
    """
    Move a handle (role is applied to the handle)
    """

    GLUE_DISTANCE = 10

    def __init__(self, item, handle, view):
        self.item = item
        self.handle = handle
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, pos):
        self.last_x, self.last_y = pos
        canvas = self.item.canvas

        cinfo = canvas.get_connection(self.handle)
        if cinfo:
            canvas.solver.remove_constraint(cinfo.constraint)

    def move(self, pos):
        item = self.item
        handle = self.handle
        view = self.view

        v2i = view.get_matrix_v2i(item)

        x, y = v2i.transform_point(*pos)

        self.handle.pos = (x, y)

        sink = self.glue(pos)

        # do not request matrix update as matrix recalculation will be
        # performed due to item normalization if required
        item.request_update(matrix=False)

        return sink

    def stop_move(self):
        pass

    def glue(self, pos, distance=GLUE_DISTANCE):
        """
        Glue to an item near a specific point.

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

            connector = Connector(self.item, self.handle)
            sink = ConnectionSink(connectable, port)

            if connector.allow(sink):
                # transform coordinates from view space to the item
                # space and update position of item's handle
                v2i = view.get_matrix_v2i(item).transform_point
                handle.pos = v2i(*glue_pos)
                return sink
        return None


HandleInMotion = generic(ItemHandleInMotion)


class ItemConnector(object):

    GLUE_DISTANCE = 10  # Glue distance in view points

    def __init__(self, item, handle):
        self.item = item
        self.handle = handle

    def allow(self, sink):
        return True

    def glue(self, sink):
        """
        Glue the Connector handle on the sink's port.
        """
        handle = self.handle
        item = self.item
        matrix = item.canvas.get_matrix_i2i(item, sink.item)
        pos = matrix.transform_point(*handle.pos)
        gluepos, dist = sink.port.glue(pos)
        matrix.invert()
        handle.pos = matrix.transform_point(*gluepos)

    def connect(self, sink):
        """
        Connect the handle to a sink (item, port).

        Note that connect() also takes care of disconnecting in case a
        handle is reattached to another element.
        """

        cinfo = self.item.canvas.get_connection(self.handle)

        # Already connected? disconnect first.
        if cinfo:
            self.disconnect()

        if not self.allow(sink):
            return

        self.glue(sink)

        self.connect_handle(sink)

    def connect_handle(self, sink, callback=None):
        """
        Create constraint between handle of a line and port of
        connectable item.

        :Parameters:
         sink
            Connectable item and port.
         callback
            Function to be called on disconnection.
        """
        canvas = self.item.canvas
        handle = self.handle
        item = self.item

        constraint = sink.port.constraint(canvas, item, handle, sink.item)

        canvas.connect_item(
            item, handle, sink.item, sink.port, constraint, callback=callback
        )

    def disconnect(self):
        """
        Disconnect the handle from the attached element.
        """
        self.item.canvas.disconnect_item(self.item, self.handle)


Connector = generic(ItemConnector)


class ItemConnectionSink(object):
    """
    This role should be applied to items that is connected to.
    """

    def __init__(self, item, port):
        self.item = item
        self.port = port

    def find_port(self, pos):
        """
        Glue to the closest item on the canvas.
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


ConnectionSink = generic(ItemConnectionSink)


##
## Painter aspects
##


class ItemPaintFocused(object):
    """
    Paints on top of all items, just for the focused item and only
    when it's hovered (see gaphas.painter.FocusedItemPainter)
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def paint(self, context):
        pass


PaintFocused = generic(ItemPaintFocused)


# vim:sw=4:et:ai
