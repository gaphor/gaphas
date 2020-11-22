#############
API reference
#############

The API can be separated into a [Model-View-Controller](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller) with these three parts:

1. The Model, including the canvas and items
2. The View, called view
3. The Controller, called tools

Canvas and Items
================

Class: ``gaphas.canvas.Canvas``
------

The ``Canvas`` is a container for items.

.. code-block: python

    canvas = Canvas()

Class: ``gaphas.item.Item``
------

Base class (or interface) for items on a ``Canvas``.

.. code-block: python

    item = Item()

Properties
~~~~~~~~~~

- ``matrix``: The item's transformation matrix
- ``canvas``: The canvas, which owns an item
- ``constraints``: list of item constraints, automatically registered when the item is added to a canvas; may be extended in subclasses

Class: ``gaphas.connector.Handle``
------

Handles are used to support modifications of Items.

If the handle is connected to an item, the ``connected_to`` property should refer to the item. A ``disconnect`` handler should
be provided that handles the required disconnect behaviour, for example, cleaning up the constraints and ``connected_to``.

- pos (``gaphas.connector.Position``): The position of the item, default value is (0, 0).
- strength (int): The strength of the handle to use in the constraint solver; default value is NORMAL, which is 20.
- connectable (bool): Makes the handle connectable to other items; default value is False.
- movable (bool): Makes the handle moveable; default value is True.

.. code-block: python

    handle = Handle((10, 10), connectable=True)

Class: ``gaphas.connector.LinePort``
------

The Line Port is part of an item that provides a line between two handles.

- start (``gaphas.connector.Position``): The start position of the line.
- end (``gaphas.connector.Position``): The end position of the line.

.. code-block: python

    p1, p2 = (0.0, 0.0), (100.0, 100.0)
    port = LinePort(p1, p2)

Class: ``gaphas.connector.PointPort``
------

The Point Port connects the handle to an item using a port at the location of the handle.

.. code-block: python

    h = Handle((10, 10))
    port = PointPort(h.pos)

Class: ``gaphas.solver.Solver``
------

A Solver solves constraints.

.. code-block: python

    a, b, c = Variable(1.0), Variable(2.0), Variable(3.0)
    solver = Solver()
    c_eq = EquationConstraint(lambda a,b: a+b, a=a, b=b)
    solver.add_constraint(c_eq)

Class: ``gaphas.constraint.EqualsConstraint``
------

Make 'a' and 'b' equal.

.. code-block: python

    a, b = Variable(1.0), Variable(2.0)
    eq = EqualsConstraint(a, b)
    eq.solve_for(a)

Class: ``gaphas.constraint.LessThanConstraint``
------

Ensure one variable stays smaller than another.

.. code-block: python

    a, b = Variable(3.0), Variable(2.0)
    lt = LessThanConstraint(smaller=a, bigger=b)
    lt.solve_for(a)

Class: ``gaphas.constraint.CenterConstraint``
------

Ensures a Variable is kept between two other variables.

.. code-block: python

    a, b, center = Variable(1.0), Variable(3.0), Variable()
    eq = CenterConstraint(a, b, center)
    eq.solve_for(a)

Class: ``gaphas.constraint.EquationConstraint``
------

Solve a linear equation.

.. code-block: python

    a, b, c = Variable(), Variable(4), Variable(5)
    cons = EquationConstraint(lambda a, b, c: a + b - c, a=a, b=b, c=c)
    cons.solve_for(a)

Class: ``gaphas.constraint.BalanceConstraint``
------

Keeps three variables in line, maintaining a specific ratio.

.. code-block: python

    a, b, c = Variable(2.0), Variable(3.0), Variable(2.3, WEAK)
    bc = BalanceConstraint(band=(a,b), v=c)
    c.value = 2.4

Class: ``gaphas.constraint.LineConstraint``
------

Solves the equation where a line is connected to a line or side at a specific point.

.. code-block: python

    line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
    point = (Variable(15), Variable(4))
    lc = LineConstraint(line=line, point=point)

### View

Class: ``gaphas.view.View``
------

View class for ``gaphas.canvas.Canvas`` objects.

.. code-block: python

    canvas = Canvas()
    view = View(canvas=canvas)

Class: ``gaphas.view.GtkView``
------

GTK+ widget for rendering a ``gaphas.canvas.Canvas`` to a screen.

.. code-block: python

    canvas = Canvas()
    win = Gtk.Window()
    view = GtkView(canvas=canvas)
    win.add(view)

Class: ``gaphas.painter.PainterChain``
------

Chain up a set of painters.

.. code-block: python

    view.painter = (
        PainterChain()
        .append(FreeHandPainter(ItemPainter()))
        .append(HandlePainter())
        .append(FocusedItemPainter())
    )

Class: ``gaphas.painter.DrawContext``
------

Special context for drawing the item. It contains a cairo context and properties like selected and focused.

- **kwargs: Optional cairo properties for a context.

.. code-block: python

    DrawContext(
        painter=self,
        cairo=cairo,
        selected=(item in view.selection.selected_items),
        focused=(item is view.selection.focused_item),
        hovered=(item is view.selection.hovered_item),
        dropzone=(item is view.selection.dropzone_item),
        draw_all=self.draw_all,
    )

Class: ``gaphas.painter.ItemPainter``
------

Painter to draw an item.

.. code-block: python


    svgview = View(view.canvas)
    svgview.painter = ItemPainter()

Class: ``gaphas.painter.CairoBoundingBoxContext``
------

It is used to intercept ``stroke()``, ``fill()``, and other context operations so that the bounding box of the item involved can be calculated.

- cairo (cairo.Context): The cairo context to intercept.

.. code-block: python

    cairo = CairoBoundingBoxContext(cairo)

Class: ``gaphas.painter.BoundingBoxPainter``
------

A type of ItemPainter which is used to calculate the bounding boxes (in canvas coordinates) for the items.

.. code-block: python

    view.bounding_box_painter = BoundingBoxPainter()

Class: ``gaphas.painter.HandlePainter``
------

Draw handles of items that are marked as selected in the view.

Class: ``gaphas.painter.FocusedItemPainter``
------

Used to draw on top of all the other layers for the focused item.

### Tools

Interacting with the View is done through tools.
Tools tell _what_ has to be done (like moving).
To make an element move aspects are defined.
Aspects tell how the behaviour has to be performed.

Class: ``gaphas.tool.hover_tool``
------

Makes the item under the mouse cursor the hovered item.

- view (``gaphas.view.View``): The view to use for the tool; default is None.

Class: ``gaphas.toolitem_tool``
------

Does selection and dragging of items and handles.

- view (``gaphas.view.View``): The view to use for the tool; default is None.

Class: ``gaphas.tool.rubberband_tool``
------

Allows the user to drag a "rubber band" for selecting items in an area.

- view (``gaphas.view.View``): The view to use for the tool; default is None.

Class: ``gaphas.tool.pan_tool``
------

Captures drag events with the middle mouse button and uses them to translate the Canvas within the view.

- view (``gaphas.view.View``): The view to use for the tool; default is None.

Class: ``gaphas.tool.zoom_tool``
------

- view (``gaphas.view.View``): The view to use for the tool; default is None.

Class: ``gaphas.tool.placement_tool``
------

Tool for placing items on the Canvas.

- view (``gaphas.view.View``): The view to use for the tool.
- factory (factory object): A Canvas item factory for creating new items.
- handle_tool (``gaphas.tools.HandleTool``): The handle tool to use.
- handle_index (int): The index of the handle to be used by the handle tool.

.. code-block: python

    def on_clicked(button):
        view.tool.grab(PlacementTool(view, factory(view, MyLine), HandleTool(view), 1))

Class: ``gaphas.aspects.ItemFinder``
------

Find an item on the Canvas.

- view (``gaphas.view.View``): The view to use in order to search for an item.

Class: ``gaphas.aspects.ItemSelection``
------

Manages selection and unselection of items.

- item (``gaphas.item.Item``): The item to set as focused or unfocused.
- view (``gaphas.view.View``): The view to focus or unfocus on.

Class: ``gaphas.aspects.ItemInMotion``
------

Manages motion of an item.

- item (``gaphas.item.Item``): The item to move.
- view (``gaphas.view.View``): The view to to use for move coordinates.

Class: ``gaphas.aspects.ItemHandleFinder``
------

Finds handles.

- item (``gaphas.item.Item``): The item.
- view (``gaphas.view.View``): The view to get the handle at the position from.

.. code-block: python

    canvas = Canvas()
    line = Line()
    canvas.add(line)
    view = View(canvas)
    finder = HandleFinder(line, view)

Class: ``gaphas.aspects.ElementHandleSelection``
------

Selects the handle of a ``gaphas.item.Element``.

- item (``gaphas.item.Item``): The Element item that the handle belongs to.
- handle (``gaphas.connector.Handle``): The handle to select or unselect.
- view (``gaphas.view.View``): The view that can be used to apply the cursor to.

Class: ``gaphas.aspects.ItemHandleInMotion``
------

Move a handle.

- item (``gaphas.item.Item``): The item that the handle belongs to.
- handle (``gaphas.connector.Handle``): The handle to move.
- view (``gaphas.view.View``): The view to use for the coordinate system.

Class: ``gaphas.aspects.ItemConnector``
------

Connect or disconnect an item's handle to another item or port.

- item (``gaphas.item.Item``): The item that the handle belongs to.
- handle (``gaphas.connector.Handle``): The handle to connect.

Class: ``gaphas.aspects.ItemConnectionSink``
------

Makes an item a sink, which is another item that an item's handle is connected to like a connected item or port.

- item (``gaphas.item.Item``): The item to look for ports on.
- port (``gaphas.connector.Port``): The port to use as the sink.

Class: ``gaphas.aspects.ItemPaintFocused``
------

Paints on top of all items, just for the focused item and only when it's hovered (see
 ``gaphas.painter.FocusedItemPainter``).

- item (``gaphas.item.Item``): The focused item.
- view (``gaphas.view.View``): The view to paint with.

### Extended Behaviour

By importing the following modules, extra behaviour is added to the default view behaviour.

Class: ``gaphas.segment.LineSegment``
------

Split and merge line segments.

- item (``gaphas.item.Item``): The item of the segment.
- view (``gaphas.view.View``): The view to use for the split coordinate system.

Class: ``gaphas.segment.SegmentHandleFinder``
------

Extends the ``gaphas.aspects.ItemHandleFinder`` to find a handle on a line, and create a new handle if the mouse is located between two handles. The position aligns with the points drawn by the SegmentPainter.

- item (``gaphas.item.Item``): The item.
- view (``gaphas.view.View``): The view to get the handle at the position from.

Class: ``gaphas.segment.SegmentHandleSelection``
------

Extends the ``gaphas.aspects.ItemHandleSelection`` to merge segments if the handle is released.

- item (``gaphas.item.Item``): The item that the handle belongs to.
- handle (``gaphas.connector.Handle``): The handle to select or unselect.
- view (``gaphas.view.View``): The view to use to apply the cursor to.

Class: ``gaphas.segment.LineSegmentPainter``
------

This painter draws pseudo-handles on a ``gaphas.item.Line`` by extending ``gaphas.aspects.ItemPaintFocused``. Each line can be split by dragging those points, which will result in a new handle.

ConnectHandleTool takes care of performing the user interaction required for this feature.

- item (``gaphas.item.Item``): The focused item.
- view (``gaphas.view.View``): The view to paint with.

Class: ``gaphas.guide.ElementGuide``
------

Provides a guide to align items for ``gaphas.item.Element``.

- item (``gaphas.item.Item``): The item to provide guides for.

Class: ``gaphas.guide.LineGuide``
-------------------------------

Provides a guide to align items for ``gaphas.item.Line``.

- item (``gaphas.item.Item``): The item to provide guides for.

Class: ``gaphas.guide.GuidedItemInMotion``
----------------------------------------

Move the item and lock the position of any element that's located at the same position.

- item (``gaphas.item.Item``): The item to move.
- view (``gaphas.view.View``): The view with guides to use for move coordinates.

.. code-block:: python
    canvas = Canvas()
    view = GtkView(canvas)
    element = Element()
    guider = GuidedItemInMotion(element, view)
    guider.start_move((0, 0))


Class: ``gaphas.guide.GuidedItemHandleInMotion``
----------------------------------------------

Move a handle and lock the position of any element that's located at the same position.

- item (``gaphas.item.Item``): The item that the handle belongs to.
- handle (``gaphas.connector.Handle``): The handle to move.
- view (``gaphas.view.View``): The view with guides to use for the coordinate system.

Class: ``gaphas.guide.GuidePainter``
------

Paints on top of all items with guides, just for the focused item and only when it's hovered.

- item (``gaphas.item.Item``): The focused item.
- view (``gaphas.view.View``): The view with guides to paint with.

Miscellaneous
=============

Class: ``gaphas.tree.Tree``
------

A Tree structure with the nodes stored in a depth-first order.

.. code-block:: python

    tree = Tree()
    tree.add("node1")
    tree.add("node2", parent="node1")


Class: ``gaphas.matrix.Matrix``
------

Adds @observed messages on state changes to the cairo.Matrix.

- xx (float): xx component of the affine transformation
- yx (float): yx component of the affine transformation
- xy (float): xy component of the affine transformation
- yy (float): yy component of the affine transformation
- x0 (float): X translation component of the affine transformation
- y0 (float): Y translation component of the affine transformation

.. code-block:: python

    matrix = Matrix(1, 0, 0, 1, 0, 0)


Class: ``gaphas.table.Table``
------

Table is a storage class that can be used to store information, like one would in a database table, with indexes on the desired "columns." It includes indexing and is optimized for lookups.

- columns (tuple): The columns of the table.
- index (tuple):

.. code-block:: python

    from collections import namedtuple
    C = namedtuple('C', "foo bar baz")
    s = Table(C, (2,))


Class: ``gaphas.quadtree.Quadtree``
------

A quadtree is a tree data structure in which each internal node has up to four children. Quadtrees are most often used to partition a two

- bounds (tuple): The boundaries of the quadtree (x, y, width, height).
- capacity (int); The number of elements in one tree bucket; default is 10.

.. code-block:: python

    qtree = Quadtree((0, 0, 100, 100))


Class: ``gaphas.geometry.Rectangle``
------

Rectangle object which can be added (union), substituted (intersection), and points and rectangles can be tested to be in the rectangle.

- x (int): X position of the rectangle.
- y (int): Y position of the rectangle.
- width (int): Width of the rectangle.
- height (int): Hiehgt of the rectangle.

.. code-block:: python

    rect = Rectangle(1, 1, 5, 5)


Decorator: ``@AsyncIO``
----------

Schedule an idle handler at a given priority.

- single (bool): Schedules the decorated function to be called only a single time.
- timeout (int): The time between calls of the decorated function.
- priority (int): The GLib.PRIORITY constant to set the event priority.

.. code-block:: python

    @AsyncIO(single=True, timeout=60)
    def c2(self):
        print('idle-c2', GLib.main_depth())


Decorator: ``@nonrecursive``
----------

Enforces a function or method to not be executed recursively.
   api/decorators

.. code-block:: python

    class A(object):
        @nonrecursive
        def a(self, x=1):
            self.a(x+1)

Decorator: ``@recursive``
----------

Limits the recursion for a specific function.

- limit (int): The limit for the number of recursive loops a function can be called; default is 10000.

.. code-block:: python

    @recursive(10)
    def a(self, x=0):
        self.a()
