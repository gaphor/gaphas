"""
Defines aspects for Items. Aspects form intermediate items between tools
and items.
"""

import sys
from gaphas.item import Item
from gaphas.connector import Handle


class Aspect(object):
    """
    Aspects are intermediate objects that act between a Tool and an Item.
    """
    # _regs = {} # class -> aspect map; defined by @aspectfactory

    @classmethod
    def _lookup(cls, itemcls):
        try:
            regs = cls._regs
        except AttributeError:
            raise TypeError("No factory class defined for aspect %s" % cls)
        for c in itemcls.__mro__:
            try:
                return regs[c]
            except KeyError:
                pass
        else:
            raise TypeError("class %s can not be instantiated through %s" % (cls, itemcls))

    def __new__(cls, item, *args, **kwargs):
        aspectcls = cls._lookup(type(item))
        return super(Aspect, cls).__new__(aspectcls, item, *args, **kwargs) 


def aspectfactory(cls):
    """
    Define class as the toplevel aspect
    """
    cls._regs = {}
    return cls


def aspect(itemcls):
    """
    Aspect decorator.
    """
    def wrapper(cls):
        cls._regs[itemcls] = cls
        return cls
    return wrapper


@aspect(Item)
@aspectfactory
class Selection(object):
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
@aspectfactory
class InMotion(object):

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


@aspect(Handle)
@aspectfactory
class HandleSelection(object):
    """
    Deal with selection of the handle.
    """

    def __init__(self, handle, view):
        self.handle = handle
        self.view = view

    def select(self):
        pass

    def unselect(self):
        pass


@aspect(Item)
@aspectfactory
class HandleInMotion(object):
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
@aspectfactory
class Connector(object):

    def __init__(self, item, handle):
        self.item = item
        self.handle = handle

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
@aspectfactory
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


# vim:sw=4:et:ai
