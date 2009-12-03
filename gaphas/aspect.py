"""
Defines aspects for Items. Aspects form intermediate items between tools
and items.
"""

import sys
import gtk.gdk
from simplegeneric import generic
from gaphas.item import Item, Line, Element
from gaphas.connector import Handle
from gaphas.geometry import distance_point_point_fast, distance_line_point


@generic
def Selection(item, view):
    raise TypeError


@Selection.when_type(Item)
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


@generic
def InMotion(item, view):
    raise TypeError


@InMotion.when_type(Item)
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


@generic
def HandleFinder(item, view):
    raise TypeError


@HandleFinder.when_object(None)
@HandleFinder.when_type(Item)
class ItemHandleFinder(object):
    """
    Deals with the task of finding handles.
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos):
        return self.view.get_handle_at_point(pos)


@generic
def HandleSelection(item, handle, view):
    raise TypeError


@HandleSelection.when_type(Item)
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

@HandleSelection.when_type(Element)
class ElementHandleSelection(ItemHandleSelection):
    CURSORS = (
            gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_CORNER),
            gtk.gdk.Cursor(gtk.gdk.TOP_RIGHT_CORNER),
            gtk.gdk.Cursor(gtk.gdk.BOTTOM_RIGHT_CORNER),
            gtk.gdk.Cursor(gtk.gdk.BOTTOM_LEFT_CORNER) )

    def select(self):
        index = self.item.handles().index(self.handle)
        if index < 4:
            self.view.window.set_cursor(self.CURSORS[index])

    def unselect(self):
        from view import DEFAULT_CURSOR
        cursor = gtk.gdk.Cursor(DEFAULT_CURSOR)
        self.view.window.set_cursor(cursor)



@generic
def HandleInMotion(item, handle, view):
    raise TypeError


@HandleInMotion.when_type(Item)
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

        connectable, port, glue_pos = \
                view.get_port_at_point(pos, distance=distance, exclude=(item,))

        # check if item and found item can be connected on closest port
        if port is not None:
            assert connectable is not None

            connector = Connector(self.item, self.handle)
            sink = ConnectionSink(connectable, port)

            if connector.allow(sink):
                # transform coordinates from view space to the item space and
                # update position of item's handle
                v2i = view.get_matrix_v2i(item).transform_point
                handle.pos = v2i(*glue_pos)
                return sink
        return None


@generic
def Connector(item, handle):
    raise TypeError


@Connector.when_type(Item)
class ItemConnector(object):

    GLUE_DISTANCE = 10 # Glue distance in view points

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

        Note that connect() also takes care of disconnecting in case a handle
        is reattached to another element.
        """
        if not self.allow(sink):
            return

        # Ensure the handle is not connected to some other element
        if canvas.get_connection(self.handle):
            self.disconnect()

        self.glue(sink)

        self.connect_handle(sink)


    def connect_handle(self, sink, callback=None):
        """
        Create constraint between handle of a line and port of connectable
        item.

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

        canvas.connect_item(item, handle, sink.item, sink.port,
            constraint, callback=callback)


    def disconnect(self):
        """
        Disconnect the handle from the attached element.
        """
        self.item.canvas.disconnect_item(self.item, self.handle)


@generic
def ConnectionSink(item, port):
    raise TypeError


@ConnectionSink.when_type(Item)
class ConnectionSink(object):
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


##
## Fancy features for Lines
##

@generic
def Segment(item, view):
    raise TypeError


@Segment.when_type(Line)
class LineSegment(object):

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def split(self, pos):
        item = self.item
        handles = item.handles()
        x, y = self.view.get_matrix_v2i(item).transform_point(*pos)
        for h1, h2 in zip(handles, handles[1:]):
            xp = (h1.pos.x + h2.pos.x) / 2
            yp = (h1.pos.y + h2.pos.y) / 2
            if distance_point_point_fast((x,y), (xp, yp)) <= 4:
                segment = handles.index(h1)
                handles, ports = self.split_segment(segment)
                return handles and handles[0]

    def split_segment(self, segment, count=2):
        """
        Split one item segment into ``count`` equal pieces.

        Two lists are returned

        - list of created handles
        - list of created ports

        :Parameters:
         segment
            Segment number to split (starting from zero).
         count
            Amount of new segments to be created (minimum 2). 
        """
        item = self.item
        if segment < 0 or segment >= len(item.ports()):
            raise ValueError('Incorrect segment')
        if count < 2:
            raise ValueError('Incorrect count of segments')

        def do_split(segment, count):
            handles = item.handles()
            p0 = handles[segment].pos
            p1 = handles[segment + 1].pos
            dx, dy = p1.x - p0.x, p1.y - p0.y
            new_h = item._create_handle((p0.x + dx / count, p0.y + dy / count))
            item._reversible_insert_handle(segment + 1, new_h)

            p0 = item._create_port(p0, new_h.pos)
            p1 = item._create_port(new_h.pos, p1)
            item._reversible_remove_port(item.ports()[segment])
            item._reversible_insert_port(segment, p0)
            item._reversible_insert_port(segment + 1, p1)

            if count > 2:
                do_split(segment + 1, count - 1)

        do_split(segment, count)

        # force orthogonal constraints to be recreated
        item._update_orthogonal_constraints(item.orthogonal)

        self._recreate_constraints()

        handles = item.handles()[segment + 1:segment + count]
        ports = item.ports()[segment:segment + count - 1]
        return handles, ports


    def merge_segment(self, segment, count=2):
        """
        Merge two (or more) item segments.

        Tuple of two lists is returned, list of deleted handles and list of
        deleted ports.

        :Parameters:
         segment
            Segment number to start merging from (starting from zero).
         count
            Amount of segments to be merged (minimum 2). 
        """
        item = self.item
        if len(item.ports()) < 2:
            raise ValueError('Cannot merge item with one segment')
        if segment < 0 or segment >= len(item.ports()):
            raise ValueError('Incorrect segment')
        if count < 2 or segment + count > len(item.ports()):
            raise ValueError('Incorrect count of segments')

        # remove handle and ports which share position with handle
        deleted_handles = item.handles()[segment + 1:segment + count]
        deleted_ports = item.ports()[segment:segment + count]
        for h in deleted_handles:
            item._reversible_remove_handle(h)
        for p in deleted_ports:
            item._reversible_remove_port(p)

        # create new port, which replaces old ports destroyed due to
        # deleted handle
        p1 = item.handles()[segment].pos
        p2 = item.handles()[segment + 1].pos
        port = item._create_port(p1, p2)
        item._reversible_insert_port(segment, port)

        # force orthogonal constraints to be recreated
        item._update_orthogonal_constraints(item.orthogonal)

        self._recreate_constraints()

        return deleted_handles, deleted_ports


    def _recreate_constraints(self):
        """
        Create connection constraints between connecting lines and an item.

        :Parameters:
         connected
            Connected item.
        """
        connected = self.item
        def find_port(line, handle, item):
            #port = None
            #max_dist = sys.maxint
            canvas = item.canvas

            ix, iy = canvas.get_matrix_i2i(line, item).transform_point(*handle.pos)

            # find the port using item's coordinates
            sink = ConnectionSink(item, None)
            return sink.find_port((ix, iy))

        if not connected.canvas:
            # No canvas, no constraints
            return

        canvas = connected.canvas
        for cinfo in list(canvas.get_connections(connected=connected)):
            item, handle = cinfo.item, cinfo.handle
            port = find_port(item, handle, connected)
            
            constraint = port.constraint(canvas, item, handle, connected)

            cinfo = canvas.get_connection(handle)
            canvas.reconnect_item(item, handle, constraint=constraint, callback=cinfo.callback)


@HandleFinder.when_type(Line)
class SegmentHandleFinder(ItemHandleFinder):
    """
    Find a handle on a line, create a new one if the mouse is located
    between two handles. The position aligns with the points drawn by
    the SegmentPainter.
    """

    def get_handle_at_point(self, pos):
        view = self.view
        item = view.hovered_item
        handle = None
        if self.item is view.focused_item:
            try:
                segment = Segment(self.item, self.view)
            except TypeError:
                pass
            else:
                handle = segment.split(pos)

        if not handle:
            item, handle = super(SegmentHandleFinder, self).get_handle_at_point(pos)
        return item, handle


@HandleSelection.when_type(Line)
class SegmentHandleSelection(ItemHandleSelection):
    """
    In addition to the default behaviour, merge segments if the handle is
    released.
    """

    def unselect(self):
        item = self.item
        handle = self.handle
        handles = item.handles()

        # don't merge using first or last handle
        if handles[0] is handle or handles[-1] is handle:
            return True

        handle_index = handles.index(handle)
        segment = handle_index - 1

        # cannot merge starting from last segment
        if segment == len(item.ports()) - 1:
            segment =- 1
        assert segment >= 0 and segment < len(item.ports()) - 1

        before = handles[handle_index - 1]
        after = handles[handle_index + 1]
        d, p = distance_line_point(before.pos, after.pos, handle.pos)

        if d < 2:
            assert len(self.view.canvas.solver._marked_cons) == 0
            Segment(item, self.view).merge_segment(segment)

        if handle:
            item.request_update()

# vim:sw=4:et:ai
