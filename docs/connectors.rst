Connections
===========
A Port defines a connectable part of an item. Handles can connect to ports to make connections between items.

Constraints
-----------
Diagram items can have internal constraints, which can be used to position
item's ports within an item itself.

For example, `Element` item could create constraints to position ports over
its edges of rectanglular area. The result is duplication of constraints as
`Element` already constraints position of handles to keep them in
a rectangle.

For example, a horizontal line could be implemented like::

    class HorizontalLine(gaphas.item.Item):
        def __init__(self, connections: gaphas.connections.Connections):
            super(HorizontalLine, self).__init__()

            self.start = Handle()
            self.end = Handle()

            self.port = LinePort(self.start.pos, self.end.pos)

            connections.add_constraint(self,
                constraint(horizontal=(self.start.pos, self.end.pos)))

Connections
-----------
Connection between two items is established by creating a constraint
between handle's position and port's positions (positions are constraint
solver variables).

To create a constraint between two items, the constraint needs a common
coordinate space (each item has it's own origin coordinate).
This can be done with the `gaphas.position.MatrixProjection` class, which
translates coordinates to a common ("canvas") coordinate space where they can
be used to connect two different items.

Examples of ports can be found in Gaphas and Gaphor source code

- `gaphas.item.Line` and `gaphas.item.Element` classes
- Gaphor interface and lifeline items have own specific ports
