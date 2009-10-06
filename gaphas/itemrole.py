"""
Defines roles for Items. Roles are a means to add behaviour to an item.
"""

from roles import RoleType

class Selection(object):
    """
    A role for items. When dealing with selection.

    Behaviour can be overridden by applying the @assignto decorator
    to a subclass.
    """
    __metaclass__ = RoleType

    def focus(self, context):
        """
        Set selection on the view.
        """
        context.view.focused_item = self

    def unselect(self, context):
        context.view.focused_item = None
        context.view.unselect_item(self)

    def move(self, dx, dy):
        self.matrix.translate(dx, dy)
        self.canvas.request_matrix_update(self)


class HandleSelection(object):
    __metaclass__ = RoleType

    def focus(self, context):
        view = context.view
        handle = context.handle
        view.focused_item = self
        context.grabbed_handle = handle

    def move(self, dx, dy):
        pass


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
        data = canvas.get_connection_data(self, handle)
        if data:
            canvas.solver.remove_constraint(data[0])

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

    def glue(self, pos):
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
