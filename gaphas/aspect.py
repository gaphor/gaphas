"""
Defines aspects for Items. Aspects form intermediate items between tools
and items.
"""

import sys
from gaphas.item import Item, Line
from gaphas.connector import Handle
from gaphas.geometry import distance_point_point_fast, distance_line_point

class Aspect(object):
    """
    Aspects are intermediate objects that act between a Tool and an Item.

    Aspects should define of what they are aspects by using the @aspect
    decorator.
    """
    # _aspect_register = {} # class -> aspect map; defined by @aspect

    @classmethod
    def _lookup(cls, material):
        try:
            regs = cls._aspect_register
        except AttributeError:
            raise TypeError("No factory class defined for aspect %s" % cls)
        for c in material.__mro__:
            try:
                return regs[c]
            except KeyError:
                pass
        raise TypeError("class %s can not be instantiated through %s" % (cls, material))

    def __new__(cls, item, *args, **kwargs):
        #print 'aspect:', cls, item, args, kwargs
        aspectcls = cls._lookup(type(item))
        #return super(Aspect, cls).__new__(aspectcls, item, *args, **kwargs) 
        new = super(Aspect, cls).__new__(aspectcls)
        print 'aspect:', item, '->', new
        return new
        #return object.__new__(aspectcls)


def aspect(*material):
    """
    Aspect decorator.
    """
    def wrapper(cls):
        for c in material:
            try:
                cls._aspect_register[c] = cls
            except AttributeError:
                cls._aspect_register = { c: cls }
        return cls
    return wrapper


@aspect(Item)
class Selection(Aspect):
    """
    A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @assignto decorator
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


@aspect(Item)
class InMotion(Aspect):

    def __init__(self, item, view):
        self.item = item
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, x, y):
        self.last_x, self.last_y = x, y

    def move(self, x, y):
        """
        Move the item. x and y are in view coordinates.
        """
        item = self.item
        view = self.view
        v2i = view.get_matrix_v2i(item)

        dx, dy = x - self.last_x, y - self.last_y
        dx, dy = v2i.transform_distance(dx, dy)
        self.last_x, self.last_y = x, y

        item.matrix.translate(dx, dy)
        item.canvas.request_matrix_update(item)


@aspect(type(None), Item)
class HandleFinder(Aspect):
    """
    Deals with the task of finding handles.
    """

    def __init__(self, item, view):
        self.item = item
        self.view = view

    def get_handle_at_point(self, pos):
        return self.view.get_handle_at_point(pos)


@aspect(Item)
class HandleSelection(Aspect):
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


@aspect(Item)
class HandleInMotion(Aspect):
    """
    Move a handle (role is applied to the handle)
    """

    def __init__(self, item, handle, view):
        self.item = item
        self.handle = handle
        self.view = view
        self.last_x, self.last_y = None, None

    def start_move(self, x, y):
        self.last_x, self.last_y = x, y

    def move(self, x, y):
        item = self.item
        handle = self.handle
        view = self.view

        v2i = view.get_matrix_v2i(item)

        x, y = v2i.transform_point(x, y)

        self.handle.pos = (x, y)

        # TODO: GLUE

        # do not request matrix update as matrix recalculation will be
        # performed due to item normalization if required
        item.request_update(matrix=False)


@aspect(Item)
class Connector(Aspect):

    GLUE_DISTANCE = 10 # Glue distance in view points

    def __init__(self, item, handle, view):
        self.item = item
        self.handle = handle
        self.view = view

    def allow(self, sink):
        """
        Return True if a connection is allowed. False otherwise.
        """
        return True

    def glue(self, pos, distance=GLUE_DISTANCE):
        """
        Glue to an item near a specific point. Returns a ConnectionSink or None
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

            sink = ConnectionSink(connectable, port)

            if self.allow(sink):
                # transform coordinates from view space to the item space and
                # update position of item's handle
                v2i = view.get_matrix_v2i(item).transform_point
                handle.pos = v2i(*glue_pos)
                return sink
        return None

    def connect(self, sink):
        # low-level connection
        self.connect_handle(self.item, self.handle, sink.item, sink.port)

        # connection in higher level of application stack
        #self.post_connect(line, handle, item, port)
        pass

    def connect_handle(self, line, handle, item, port, callback=None):
        """
        Create constraint between handle of a line and port of connectable
        item.

        :Parameters:
         line
            Connecting item.
         handle
            Handle of connecting item.
         item
            Connectable item.
         port
            Port of connectable item.
         callback
            Function to be called on disconnection.
        """
        canvas = line.canvas
        solver = canvas.solver

        if canvas.get_connection(handle):
            canvas.disconnect_item(line, handle)

        constraint = port.constraint(canvas, line, handle, item)

        canvas.connect_item(line, handle, item, port,
            constraint,
            callback=callback)


    def remove_constraints(self):
        """
        Disable the constraints for a handle. The handle can then move
        freely."
        """
        canvas = self.item.canvas
        data = canvas.get_connection(self.handle)
        if data:
            canvas.solver.remove_constraint(data.constraint)


    def disconnect(self):
        """
        Disconnect the handle from.
        """
        self.item.canvas.disconnect_item(self.item, self.handle)


@aspect(Item)
class ConnectionSink(Aspect):
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

@aspect(Line)
class Segment(Aspect):

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
            print segment, len(item.ports())
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
        solver = canvas.solver
        for cinfo in list(canvas.get_connections(connected=connected)):
            item, handle = cinfo.item, cinfo.handle
            port = find_port(item, handle, connected)
            
            constraint = port.constraint(canvas, item, handle, connected)

            cinfo = canvas.get_connection(handle)
            canvas.reconnect_item(item, handle, constraint=constraint, callback=cinfo.callback)


@aspect(Line)
class SegmentHandleFinder(HandleFinder):
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


@aspect(Line)
class SegmentHandleSelection(HandleSelection):
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

        print 'release segment handle'

        handle_index = handles.index(handle)
        segment = handle_index - 1

        # cannot merge starting from last segment
        if segment == len(item.ports()) - 1:
            segment =- 1
        assert segment >= 0 and segment < len(item.ports()) - 1

        before = handles[handle_index - 1]
        after = handles[handle_index + 1]
        d, p = distance_line_point(before.pos, after.pos, handle.pos)

        print handle_index, before.pos, after.pos, handle.pos

        if d < 2:
            assert len(self.view.canvas.solver._marked_cons) == 0
            Segment(item, self.view).merge_segment(segment)

        if handle:
            item.request_update()

# vim:sw=4:et:ai
