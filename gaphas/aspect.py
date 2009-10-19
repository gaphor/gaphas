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

    def __init__(self, item):
        self.item = item

    def select(self, context):
        """
        Set selection on the view.
        """
        context.view.focused_item = self.item

    def unselect(self, context):
        context.view.focused_item = None
        context.view.unselect_item(self.item)


@aspect(Item)
@aspectfactory
class InMotion(object):

    def __init__(self, item):
        self.item = item

    def move(self, context):
        """
        Move the item. The context should contain at lease ``dx`` and ``dy``.
        """
        self.item.matrix.translate(context.dx, context.dy)
        self.item.canvas.request_matrix_update(self.item)


@aspect(Handle)
@aspectfactory
class HandleSelection(object):
    """
    Deal with selection of the handle.
    """

    def __init__(self, handle):
        self.handle = handle

    def select(self, view):
        pass

    def unselect(self, view):
        pass


@aspect(Handle)
@aspectfactory
class HandleInMotion(object):
    """
    Move a handle (role is applied to the handle)
    """

    def __init__(self, item):
        self.item = item

    def move(self, x, y):
        self.item.pos = (x, y)
        # TODO: GLUE


@aspect(Item)
@aspectfactory
class Connector(object):

    def __init__(self, item):
        self.item = item

    def connect(self, sink):
        # low-level connection
        self.connect_handle(line, handle, item, port)

        # connection in higher level of application stack
        self.post_connect(line, handle, item, port)
        pass

    def remove_constraints(self, handle):
        """
        Disable the constraints for a handle. The handle can then move
        freely."
        """
        canvas = self.item.canvas
        data = canvas.get_connection(handle)
        if data:
            canvas.solver.remove_constraint(data.constraint)


    def disconnect(self, handle):
        """
        Disconnect the handle from.
        """
        self.item.canvas.disconnect_item(self.item, handle)


@aspect(Item)
@aspectfactory
class ConnectionSink(object):
    """
    This role should be applied to items that is connected to.
    """

    def __init__(self, item):
        self.item = item

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
