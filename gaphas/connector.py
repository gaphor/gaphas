"""
Basic connectors such as Ports and Handles.
"""

__version__ = "$Revision: 2341 $"
# $HeadURL: https://svn.devjavu.com/gaphor/gaphas/trunk/gaphas/item.py $

from solver import solvable, WEAK, NORMAL, STRONG, VERY_STRONG
from state import observed, reversible_property, disable_dispatching


class Connector(object):
    """
    Basic object for connections.
    """

    _x = solvable(varname='_v_x')
    _y = solvable(varname='_v_y')

    def __init__(self, x=0, y=0, strength=NORMAL):
        self._x = x
        self._y = y
        self._x.strength = strength
        self._y.strength = strength

    @observed
    def _set_x(self, x):
        self._x = x

    x = reversible_property(lambda s: s._x, _set_x, bind={'x': lambda self: float(self.x) })
    disable_dispatching(_set_x)

    @observed
    def _set_y(self, y):
        self._y = y

    y = reversible_property(lambda s: s._y, _set_y, bind={'y': lambda self: float(self.y) })
    disable_dispatching(_set_y)

    @observed
    def _set_pos(self, pos):
        """
        Set handle position (Item coordinates).
        """
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

    def __str__(self):
        return '<%s object on (%g, %g)>' % (self.__class__.__name__, float(self._x), float(self._y))
    __repr__ = __str__

    def __getitem__(self, index):
        """
        Shorthand for returning the x(0) or y(1) component of the point.

            >>> h = Handle(3, 5)
            >>> h[0]
            Variable(3, 20)
            >>> h[1]
            Variable(5, 20)
        """
        return (self.x, self.y)[index]


class Handle(Connector):
    """
    Handles are used to support modifications of Items.

    If the handle is connected to an item, the ``connected_to`` property should
    refer to the item. A ``disconnect`` handler should be provided that handles
    all disconnect behaviour (e.g. clean up constraints and ``connected_to``).

      Note for those of you that use the Pickle module to persist a canvas:
      The property ``disconnect`` should contain a callable object (with
      __call__() method), so the pickle handler can also pickle that. Pickle is
      not capable of pickling ``instancemethod`` or ``function`` objects.
    """

    def __init__(self, x=0, y=0, strength=NORMAL, connectable=False, movable=True):
        super(Handle, self).__init__(x, y, strength)

        # Flags.. can't have enough of those
        self._connectable = connectable
        self._movable = movable
        self._visible = True
        self._connected_to = None

        # User data for the connection (e.g. constraints)
        self._connection_data = None
        # An extra property used to disconnect the constraint. Should be set
        # by the application.
        self._disconnect = None


    @observed
    def _set_connectable(self, connectable):
        self._connectable = connectable

    connectable = reversible_property(lambda s: s._connectable, _set_connectable)

    @observed
    def _set_movable(self, movable):
        self._movable = movable

    movable = reversible_property(lambda s: s._movable, _set_movable)

    @observed
    def _set_visible(self, visible):
        self._visible = visible

    visible = reversible_property(lambda s: s._visible, _set_visible)

    @observed
    def _set_connected_to(self, connected_to):
        self._connected_to = connected_to

    connected_to = reversible_property(lambda s: s._connected_to,
                                       _set_connected_to)

    @observed
    def _set_connection_data(self, connection_data):
        self._connection_data = connection_data

    connection_data = reversible_property(lambda s: s._connection_data,
                                          _set_connection_data)

    @observed
    def _set_disconnect(self, disconnect):
        self._disconnect = disconnect

    disconnect = reversible_property(lambda s: s._disconnect or (lambda: None), _set_disconnect)

    @observed
    def _set_pos(self, pos):
        """
        Set handle position (Item coordinates).
        """
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

    def __str__(self):
        return '<%s object on (%g, %g)>' % (self.__class__.__name__, float(self.x), float(self.y))
    __repr__ = __str__

    def __getitem__(self, index):
        """
        Shorthand for returning the x(0) or y(1) component of the point.

            >>> h = Handle(3, 5)
            >>> h[0]
            Variable(3, 20)
            >>> h[1]
            Variable(5, 20)
        """
        return (self.x, self.y)[index]


class Port(Connector):
    """
    A Port functions as a place on an Item where a Handle can connect.
    """

    def __init__(self, x=0, y=0, strength=NORMAL):
        super(Port, self).__init__(x, y, strength)


# vim: sw=4:et:ai
