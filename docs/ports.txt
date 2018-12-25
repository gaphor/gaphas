Ports
=====
Port is a part of an item, which defines connectable part of an item.
This concept has been introduced Gaphas version 0.4.0 to make Gaphas
connection system more flexible.

Port Types
----------
There are two types of ports implemented in Gaphor (see `gaphas.connector`
module).

First one is point port, as is often use in
`EDA <http://en.wikipedia.org/wiki/Electronic_design_automation>`_
applications, a handle connecting to such port is always kept at specific
position, which equals to port's position.

Other port type is line port. A handle connecting to such port is kept on
a line defined by start and end positions of line port.

Line port is used by items provided by `gaphas.item` module. `Element`
item has one port defined at every edge of its rectangular shape (this is 4
ports). `Line` item has one port per line segment.

Different types of ports can be invented like circle port or area port, they
should implement interface defined by `gaphas.connector.Port` class to fit
into Gaphas' connection system.

Ports and Constraints (Covering Handles)
----------------------------------------
Diagram items can have internal constraints, which can be used to position
item's ports within an item itself.

For example, `Element` item could create constraints to position ports over
its edges of rectanglular area. The result is duplication of constraints as
`Element` already constraints position of handles to keep them in
a rectangle.

*Therefore, when port covers handles, then it should reference handle
positions*.

For example, an item, which is a horizontal line could be implemented
like::

    class HorizontalLine(gaphas.item.Item):
        def __init__(self):
            super(HorizontalLine, self).__init__()

            self.start = Handle()
            self.end = Handle()

            self.port = LinePort(self.start.pos, self.end.pos)

            self.constraint(horizontal=(self.start.pos, self.end.pos))

In case of `Element` item, each line port references positions of two
handles, which keeps ports to lie over edges of rectangle. The same applies
to `Line` item - every port is defined between positions of two neighbour
handles. When `Line` item is orthogonal, then handle and ports share the
same constraints, which guard line orthogonality.

This way, item's constraints are reused and their amount is limited to
minimum.

Connections
-----------
Connection between two items is established by creating a constraint
between handle's postion and port's positions (positions are constraint
solver variables).

`ConnectHandleTool` class provides functionality to allow an user to
perform connections between items. 

Examples
--------
Examples of ports can be found in Gaphas and Gaphor source code

- `gaphas.item.Line` and `gaphas.item.Element` classes
- `gaphas.examples.PortoBox` class has an example of movable port
- Gaphor interface and lifeline items have own specific ports

