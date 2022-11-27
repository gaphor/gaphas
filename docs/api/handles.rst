Handles and Ports
=================

To connect one item to another, you need something to connect, and something to connect to.
These roles are fulfilled by ``Handle`` and ``Port``.

The Handle is an item you normally see on screen as a small square, eiter green or red.
Although the actual shape depends on the Painter_ used.

Ports represent the receiving side. A port decides if it wants a connection with a handle.
If it does, a constraint can be created and this constraint will be managed by a Connections_ instance.
It is not uncommon to create special ports to suite your application's behavior, whereas Handles are rarely subtyped.

Handle
------

.. autoclass:: gaphas.connector.Handle
   :members:

Port
----

The ``Port`` class. There are two default implementations: ``LinePort`` and ``PointPort``.

.. autoclass:: gaphas.connector.Port
   :members:

.. autoclass:: gaphas.connector.LinePort
   :members:

.. autoclass:: gaphas.connector.PointPort
   :members:

.. _Painter: painters.html#gaphas.painter.HandlePainter
.. _Connections: connections.html