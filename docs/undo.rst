Undo - implementing basic undo behaviour with Gaphas
####################################################

This document describes a basic undo system and tests Gaphas' classes with this
system.

This document contains a set of test cases that is used to prove that it really
works.

See state.txt about how state is recorded.

.. contents::

For this to work, some boilerplate has to be configured:

    >>> from gaphas import state
    >>> state.observers.clear()
    >>> state.subscribers.clear()

    >>> undo_list = []
    >>> redo_list = []
    >>> def undo_handler(event):
    ...     undo_list.append(event)
    >>> state.observers.add(state.revert_handler)
    >>> state.subscribers.add(undo_handler)

This simple undo function will revert all states collected in the undo_list:

    >>> def undo():
    ...     apply_me = list(undo_list)
    ...     del undo_list[:]
    ...     apply_me.reverse()
    ...     for e in apply_me:
    ...         state.saveapply(*e)
    ...     redo_list[:] = undo_list[:]
    ...     del undo_list[:]

Undo functionality tests
========================

The following sections contain most of the basis unit tests for undo
management.

tree.py: Tree
-------------
Tree has no observed methods.

matrix.py: Matrix
-----------------
Matrix is used by Item classes.

    >>> from gaphas.matrix import Matrix
    >>> m = Matrix()
    >>> m
    Matrix(1, 0, 0, 1, 0, 0)

translate(tx, ty):

    >>> m.translate(12, 16)
    >>> m
    Matrix(1, 0, 0, 1, 12, 16)
    >>> undo()
    >>> m
    Matrix(1, 0, 0, 1, 0, 0)

scale(sx, sy):

    >>> m.scale(1.5, 1.5)
    >>> m
    Matrix(1.5, 0, 0, 1.5, 0, 0)
    >>> undo()
    >>> m
    Matrix(1, 0, 0, 1, 0, 0)

rotate(radians):

    >>> def matrix_approx(m):
    ...     a = []
    ...     for i in tuple(m):
    ...         if -1e-10 < i < 1e-10: i=0
    ...         a.append(i)
    ...     return tuple(a)

    >>> m.rotate(0.5)
    >>> m
    Matrix(0.877583, 0.479426, -0.479426, 0.877583, 0, 0)
    >>> undo()
    >>> matrix_approx(m)
    (1.0, 0, 0, 1.0, 0, 0)

Okay, nearly, close enough IMHO...

    >>> m = Matrix()
    >>> m.translate(12, 10)
    >>> m.scale(1.5, 1.5)
    >>> m.rotate(0.5)
    >>> m
    Matrix(1.31637, 0.719138, -0.719138, 1.31637, 12, 10)
    >>> m.invert()
    >>> m
    Matrix(0.585055, -0.319617, 0.319617, 0.585055, -10.2168, -2.01515)
    >>> undo()
    >>> matrix_approx(m)
    (1.0, 0, 0, 1.0, 0, 0)

Again, rotate does not result in an exact match, but it's close enough.

    >>> undo_list
    []

canvas.py: Canvas
-----------------

    >>> from gaphas import Canvas, Item
    >>> canvas = Canvas()
    >>> canvas.get_all_items()
    []
    >>> item = Item()
    >>> canvas.add(item)

The ``request_update()`` method is observed:

    >>> len(undo_list)
    1
    >>> canvas.request_update(item)
    >>> len(undo_list)
    2

On the canvas only ``add()`` and ``remove()`` are monitored:

    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>]
    >>> item.canvas is canvas
    True
    >>> undo()
    >>> canvas.get_all_items()
    []
    >>> item.canvas is None
    True
    >>> canvas.add(item)
    >>> del undo_list[:]
    >>> canvas.remove(item)
    >>> canvas.get_all_items()
    []
    >>> undo()
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>]
    >>> undo_list
    []

Parent-child relationships are restored as well:

TODO!


    >>> child = Item()
    >>> canvas.add(child, parent=item)
    >>> child.canvas is canvas
    True
    >>> canvas.get_parent(child) is item
    True
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>, <gaphas.item.Item object at 0x...>]
    >>> undo()
    >>> child.canvas is None
    True
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>]
    >>> child in canvas.get_all_items()
    False

Now redo the previous undo action:

    >>> undo_list[:] = redo_list[:]
    >>> undo()
    >>> child.canvas is canvas
    True
    >>> canvas.get_parent(child) is item
    True
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>, <gaphas.item.Item object at 0x...>]

Remove also works when items are removed recursively (an item and it's
children):

    >>> child = Item()
    >>> canvas.add(child, parent=item)
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>, <gaphas.item.Item object at 0x...>]
    >>> del undo_list[:]
    >>> canvas.remove(item)
    >>> canvas.get_all_items()
    []
    >>> undo()
    >>> canvas.get_all_items()                          # doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>, <gaphas.item.Item object at 0x...>]
    >>> canvas.get_children(item)			# doctest: +ELLIPSIS
    [<gaphas.item.Item object at 0x...>]

As well as the reparent() method:

    >>> canvas = Canvas()
    >>> class NameItem(Item):
    ...     def __init__(self, name):
    ...         super(NameItem, self).__init__()
    ...         self.name = name
    ...     def __repr__(self):
    ...         return '<%s>' % self.name
    >>> ni1 = NameItem('a')
    >>> canvas.add(ni1)
    >>> ni2 = NameItem('b')
    >>> canvas.add(ni2)
    >>> ni3 = NameItem('c')
    >>> canvas.add(ni3, parent=ni1)
    >>> ni4 = NameItem('d')
    >>> canvas.add(ni4, parent=ni3)
    >>> canvas.get_all_items()
    [<a>, <c>, <d>, <b>]
    >>> del undo_list[:]
    >>> canvas.reparent(ni3, parent=ni2)
    >>> canvas.get_all_items()
    [<a>, <b>, <c>, <d>]
    >>> len(undo_list)
    1
    >>> undo()
    >>> canvas.get_all_items()
    [<a>, <c>, <d>, <b>]

Redo should work too:

    >>> undo_list[:] = redo_list[:]
    >>> undo()
    >>> canvas.get_all_items()
    [<a>, <b>, <c>, <d>]


Undo/redo a connection: see gaphas/tests/test_undo.py


connector.py: Handle
--------------------
Changing the Handle's position is reversible:

    >>> from gaphas import Handle
    >>> handle = Handle()
    >>> handle.pos = 10, 12
    >>> handle.pos
    <Position object on (10, 12)>
    >>> undo()
    >>> handle.pos
    <Position object on (0, 0)>

As are all other properties:

    >>> handle.connectable, handle.movable, handle.visible
    (False, True, True)
    >>> handle.connectable = True
    >>> handle.movable = False
    >>> handle.visible = False
    >>> handle.connectable, handle.movable, handle.visible
    (True, False, False)

And now undo the whole lot at once:

    >>> undo()
    >>> handle.connectable, handle.movable, handle.visible
    (False, True, True)

item.py: Item
-------------

The basic Item properties are canvas and matrix. Canvas has been tested before,
while testing the Canvas class.

The Matrix has been tested in section matrix.py: Matrix.

item.py: Element
----------------

An element has ``min_height`` and ``min_width`` properties.

    >>> from gaphas import Element
    >>> e = Element()
    >>> e.min_height, e.min_width
    (Variable(10, 100), Variable(10, 100))
    >>> e.min_height, e.min_width = 30, 40
    >>> e.min_height, e.min_width
    (Variable(30, 100), Variable(40, 100))

    >>> undo()
    >>> e.min_height, e.min_width
    (Variable(0, 100), Variable(0, 100))

    >>> canvas = Canvas()
    >>> canvas.add(e)
    >>> undo()
    >>> e.canvas

item.py: Line
-------------

A line has the following properties: ``line_width``, ``fuzziness``,
``orthogonal`` and ``horizontal``. Each one of then is observed for changes:

    >>> from gaphas import Line
    >>> from gaphas.segment import Segment
    >>> l = Line()

Let's first add a segment to the line, to test orthogonal lines as well.

    >>> segment = Segment(l, None)
    >>> _ = segment.split_segment(0)

    >>> l.line_width, l.fuzziness, l.orthogonal, l.horizontal
    (2, 0, False, False)

Now change the properties:

    >>> l.line_width = 4
    >>> l.fuzziness = 2
    >>> l.orthogonal = True
    >>> l.horizontal = True
    >>> l.line_width, l.fuzziness, l.orthogonal, l.horizontal
    (4, 2, True, True)

And undo the changes:

    >>> undo()
    >>> l.line_width, l.fuzziness, l.orthogonal, l.horizontal
    (2, 0, False, False)

In addition to those properties, line segments can be split and merged.

    >>> l.handles()[1].pos = 10, 10
    >>> l.handles()
    [<Handle object on (0, 0)>, <Handle object on (10, 10)>]

This is our basis for further testing.

    >>> del undo_list[:]

    >>> Segment(l, None).split_segment(0)      # doctest: +ELLIPSIS
    ([<Handle object on (5, 5)>], [<gaphas.connector.LinePort object at 0x...>])
    >>> l.handles()
    [<Handle object on (0, 0)>, <Handle object on (5, 5)>, <Handle object on (10, 10)>]

The opposite operation is performed with the merge_segment() method:

    >>> undo()
    >>> l.handles()
    [<Handle object on (0, 0)>, <Handle object on (10, 10)>]

Also creation and removal of connected lines is recorded and can be undone:

    >>> canvas = Canvas()
    >>> def real_connect(hitem, handle, item):
    ...     def real_disconnect():
    ...         pass
    ...     canvas.connect_item(hitem, handle, item, port=None, constraint=None, callback=real_disconnect)
    >>> b0 = Item()
    >>> canvas.add(b0)
    >>> b1 = Item()
    >>> canvas.add(b1)
    >>> l = Line()
    >>> canvas.add(l)
    >>> real_connect(l, l.handles()[0], b0)
    >>> real_connect(l, l.handles()[1], b1)
    >>> canvas.get_connection(l.handles()[0])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)
    >>> canvas.get_connection(l.handles()[1])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)

Clear already collected undo data:

    >>> del undo_list[:]

Now remove the line from the canvas:

    >>> canvas.remove(l)

The handles are disconnected:

    >>> l.canvas
    >>> canvas.get_connection(l.handles()[0])
    >>> canvas.get_connection(l.handles()[1])

Undoing the remove() action should put everything back in place again:

    >>> undo()

    >>> l.canvas                                        # doctest: +ELLIPSIS
    <gaphas.canvas.Canvas object at 0x...>
    >>> canvas.get_connection(l.handles()[0])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)
    >>> canvas.get_connection(l.handles()[1])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)


solver.py: Variable
-------------------

Variable's strength and value properties are observed:

    >>> from gaphas.solver import Variable
    >>> v = Variable()
    >>> v.value = 10
    >>> v.strength = 100
    >>> v
    Variable(10, 100)
    >>> undo()
    >>> v
    Variable(0, 20)

solver.py: Solver
-----------------

Solvers ``add_constraint()`` and ``remove_constraint()`` are observed.

    >>> from gaphas.solver import Solver
    >>> from gaphas.constraint import EquationConstraint
    >>> s = Solver()
    >>> a, b = Variable(1.0), Variable(2.0)
    >>> s.add_constraint(EquationConstraint(lambda a,b: a+b, a=a, b=b))
    EquationConstraint(<lambda>, a=Variable(1, 20), b=Variable(2, 20))
    >>> undo()

    >>> undo_list[:] = redo_list[:]
    >>> undo()
