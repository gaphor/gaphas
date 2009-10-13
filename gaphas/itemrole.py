"""
Defines roles for Items. Roles are a means to add behaviour to an item.
"""

import sys
from roles import RoleType

class Selection(object):
    """
    A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @assignto decorator
    to a subclass.
    """
    __metaclass__ = RoleType

    def select(self, context):
        """
        Set selection on the view.
        """
        context.view.focused_item = self

    def unselect(self, context):
        context.view.focused_item = None
        context.view.unselect_item(self)


class InMotion(object):
    __metaclass__ = RoleType

    def move(self, context):
        """
        Move the item. The context should contain at lease ``dx`` and ``dy``.
        """
        self.matrix.translate(context.dx, context.dy)
        self.canvas.request_matrix_update(self)


class HandleSelection(object):
    __metaclass__ = RoleType

    def find_handle(self, x, y, distance=sys.maxint):
        """
        Find a handle on the selected item. The handle is stored in
        ``context.handle``.
        """
        d = distance
        for h in self.handles():
            if not h.movable:
                continue
            hx, hy = h.pos
            if -d < (hx - x) < d and -d < (hy - y) < d:
                return h


class HandleInMotion(object):
    __metaclass__ = RoleType

    def move(self, x, y):
        self.pos = (x, y)
        # TODO: GLUE


class Connector(object):
    __metaclass__ = RoleType

    def connect(self, sink):
        pass

    def remove_constraints(self, handle):
        """
        Disable the constraints for a handle. The handle can then move
        freely."
        """
        canvas = self.canvas
        data = canvas.get_connection(handle)
        if data:
            canvas.solver.remove_constraint(data.constraint)


    def disconnect(self, handle):
        """
        Disconnect the handle from.
        """
        self.canvas.disconnect_item(self, handle)


class ConnectionSink(object):
    """
    This role should be applied to items that is connected to.
    """
    __metaclass__ = RoleType

    def find_port(self, pos):
        """
        Glue to the closest item on the canvas.
        If the item can connect, it returns a port.
        """
        port = None
        max_dist = 10e6
        for p in self.ports():
            pg, d = p.glue(pos)
            if d >= max_dist:
                continue
            port = p
            max_dist = d

        return port


# vim:sw=4:et:ai
