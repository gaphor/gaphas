State management
================

.. important:: This functionality will be removed.

A special word should be mentioned about state management. Managing state is
the first step in creating an undo system.

The state system consists of two parts:

1. A basic observer (the ``@observed`` decorator)
2. A reverser


Observer
--------

The observer simply dispatches the function called (as ``<function ..>``, not as
``<unbound method..>``!) to each handler registered in an observers list.

    >>> from gaphas import state
    >>> state.observers.clear()
    >>> state.subscribers.clear()

Let's start with creating a Canvas instance and some items:

    >>> from gaphas.canvas import Canvas
    >>> from examples.exampleitems import Circle
    >>> canvas = Canvas()
    >>> item1, item2 = Circle(), Circle()

For this demonstration let's use the Canvas class (which contains an add/remove
method pair).

It works (see how the add method automatically schedules the item for update):

    >>> def handler(event):
    ...     print('event handled', event)
    >>> state.observers.add(handler)
    >>> canvas.add(item1)                              # doctest: +ELLIPSIS
    event handled (<function Canvas.add at ...>, (<gaphas.canvas.Canvas object at ...>, <examples.exampleitems.Circle object at ...>), {})
    >>> canvas.add(item2, parent=item1)                # doctest: +ELLIPSIS
    event handled (<function Canvas.add at ...>, (<gaphas.canvas.Canvas object at ...>, <examples.exampleitems.Circle object at ...>), {'parent': <examples.exampleitems.Circle object at ...>})
    >>> list(canvas.get_all_items())                   # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>, <examples.exampleitems.Circle object at 0x...>]

Note that the handler is invoked before the actual call is made. This is
important if you want to store the (old) state for an undo mechanism.

Remember that this observer is just a simple method call notifier and knows
nothing about the internals of the ``Canvas`` class (in this case the
``remove()`` method recursively calls ``remove()`` for each of it's children).
Therefore some careful crafting of methods may be necessary in order to get the
right effect (items should be removed in the right order, child first):

    >>> canvas.remove(item1)                           # doctest: +ELLIPSIS
    event handled (<function Canvas._remove at ...>, (<gaphas.canvas.Canvas object at 0x...>, <examples.exampleitems.Circle object at 0x...>), {})
    event handled (<function Canvas._remove at ...>, (<gaphas.canvas.Canvas object at 0x...>, <examples.exampleitems.Circle object at 0x...>), {})
    >>> list(canvas.get_all_items())
    []

The ``@observed`` decorator can also be applied to properties, as is done in
gaphas/connector.py's Handle class:

    >>> from gaphas.solver import Variable
    >>> var = Variable()
    >>> var.value = 10                                  # doctest: +ELLIPSIS
    event handled (<function Variable.set_value at 0x...>, (Variable(0, 20), 10), {})

(this is simply done by observing the setter method).

Off course handlers can be removed as well (only the default revert handler
is present now):

    >>> state.observers.remove(handler)
    >>> state.observers                                 # doctest: +ELLIPSIS
    set()

What should you know:

1. The observer always generates events based on 'function' calls. Even for
   class method invocations. This is because, when calling a method (say
   Tree.add) it's the ``im_func`` field is executed, which is a function type
   object.

2. It's important to know if an event came from invoking a method or a simple
   function. With methods, the first argument always is an instance. This can
   be handy when writing an undo management systems in case multiple calls
   from the same instance do not have to be registered (e.g. if a method
   ``set_point()`` is called with exact coordinates (in stead of deltas), only
   the first call to ``set_point()`` needs to be remembered).


Reverser
--------

The reverser requires some registration.

1. Property setters should be declared with ``reversible_property()``
2. Method (or function) pairs that implement each others reverse operation
   (e.g. add and remove) should be registered as ``reversible_pair()``'s in the
   reverser engine.
   The reverser will construct a tuple (callable, arguments) which are send
   to every handler registered in the subscribers list. Arguments is a
   ``dict()``.

First thing to do is to actually enable the ``revert_handler``:

    >>> state.observers.add(state.revert_handler)

This handler is not enabled by default because:

1. it generates quite a bit of overhead if it isn't used anyway
2. you might want to add some additional filtering.

Point 2 may require some explanation. First of all observers have been added
to almost every method that involves a state change. As a result loads of
events are generated. In most cases you're only interested in the first event,
since that one contains the state before it started changing.

Handlers for the reverse events should be registered on the subscribers list:

    >>> events = []
    >>> def handler(event):
    ...     events.append(event)
    ...     print('event handler', event)
    >>> state.subscribers.add(handler)

After that, signals can be received of undoable (reverse-)events:

    >>> canvas.add(Circle())                              # doctest: +ELLIPSIS
    event handler (<function Handle._set_movable at ...>, {'self': <Handle object on (Variable(0, 20), Variable(0, 20))>, 'movable': True})
    event handler (<function Canvas._remove at ...>, {'self': <gaphas.canvas.Canvas object at 0x...>, 'item': <examples.exampleitems.Circle object at 0x...>})
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>]

As you can see this event is constructed of only two parameters: the function
that does the inverse operation of ``add()`` and the arguments that should be
applied to that function.

The inverse operation is easiest performed by the function ``saveapply()``. Of
course an inverse operation is emitting a change event too:

    >>> state.saveapply(*events.pop())                  # doctest: +ELLIPSIS
    event handler (<function Canvas.add at 0x...>, {'self': <gaphas.canvas.Canvas object at 0x...>, 'item': <examples.exampleitems.Circle object at 0x...>, 'parent': None, 'index': 0})
    >>> list(canvas.get_all_items())
    []

Just handling method pairs is one thing. Handling properties (descriptors) in
a simple fashion is another matter. First of all the original value should
be retrieved before the new value is applied (this is different from applying
the same arguments to another method in order to reverse an operation).

For this a ``reversible_property`` has been introduced. It works just like a
property (in fact it creates a plain old property descriptor), but also
registers the property as being reversible.

    >>> var = Variable()
    >>> var.value = 10                                  # doctest: +ELLIPSIS
    event handler (<function Variable.set_value at 0x...>, {'self': Variable(0, 20), 'value': 0.0})

Handlers can be simply removed:

    >>> state.subscribers.remove(handler)
    >>> state.observers.remove(state.revert_handler)

What is Observed
----------------

As far as Gaphas is concerned, only properties and methods related to the
model (e.g. ``Canvas``, ``Item``) emit state changes. Some extra effort has
been taken to monitor the ``Matrix`` class (which is from Cairo).

canvas.py:
  ``Canvas``: ``add()`` and ``remove()``

connector.py:
  ``Position``: ``x`` and ``y`` properties

  ``Handle``: ``connectable``, ``movable``, ``visible``, ``connected_to`` and ``disconnect`` properties

item.py:
  ``Item``: ``matrix`` property

  ``Element``: ``min_height`` and ``min_width`` properties

  ``Line``: ``line_width``, ``fuzziness``, ``orthogonal`` and ``horizontal`` properties

solver.py:
  ``Variable``: ``strength`` and ``value`` properties

  ``Solver``: ``add_constraint()`` and ``remove_constraint()``

matrix.py:
  ``Matrix``: ``invert()``, ``translate()``, ``rotate()`` and ``scale()``

Test cases are described in undo.txt.

Undo example
------------

This document describes a basic undo system and tests Gaphas' classes with this
system.

This document contains a set of test cases that is used to prove that it really
works.

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
    Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

translate(tx, ty):

    >>> m.translate(12, 16)
    >>> m
    Matrix(1.0, 0.0, 0.0, 1.0, 12.0, 16.0)
    >>> undo()
    >>> m
    Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

scale(sx, sy):

    >>> m.scale(1.5, 1.5)
    >>> m
    Matrix(1.5, 0.0, 0.0, 1.5, 0.0, 0.0)
    >>> undo()
    >>> m
    Matrix(1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

rotate(radians):

    >>> def matrix_approx(m):
    ...     a = []
    ...     for i in tuple(m):
    ...         if -1e-10 < i < 1e-10: i=0
    ...         a.append(i)
    ...     return tuple(a)

    >>> m.rotate(0.5)
    >>> m
    Matrix(0.8775825618903728, 0.479425538604203, -0.479425538604203, 0.8775825618903728, 0.0, 0.0)
    >>> undo()
    >>> matrix_approx(m)
    (1.0, 0, 0, 1.0, 0, 0)

Okay, nearly, close enough IMHO...

    >>> m = Matrix()
    >>> m.translate(12, 10)
    >>> m.scale(1.5, 1.5)
    >>> m.rotate(0.5)
    >>> m
    Matrix(1.3163738428355591, 0.7191383079063045, -0.7191383079063045, 1.3163738428355591, 12.0, 10.0)
    >>> m.invert()
    >>> m
    Matrix(0.5850550412602484, -0.3196170257361353, 0.3196170257361353, 0.5850550412602484, -10.216830752484334, -2.0151461037688607)
    >>> undo()
    >>> matrix_approx(m)
    (1.0, 0, 0, 1.0, 0, 0)

Again, rotate does not result in an exact match, but it's close enough.

    >>> undo_list
    []

canvas.py: Canvas
-----------------

    >>> from gaphas import Canvas
    >>> from examples.exampleitems import Circle
    >>> canvas = Canvas()
    >>> list(canvas.get_all_items())
    []
    >>> item = Circle()
    >>> canvas.add(item)

The ``request_update()`` method is observed:

    >>> len(undo_list)
    2
    >>> canvas.request_update(item)
    >>> len(undo_list)
    3

On the canvas only ``add()`` and ``remove()`` are monitored:

    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>]
    >>> undo()
    >>> list(canvas.get_all_items())
    []
    >>> canvas.add(item)
    >>> del undo_list[:]
    >>> canvas.remove(item)
    >>> list(canvas.get_all_items())
    []
    >>> undo()
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>]
    >>> undo_list
    []

Parent-child relationships are restored as well:

TODO!


    >>> child = Circle()
    >>> canvas.add(child, parent=item)
    >>> canvas.get_parent(child) is item
    True
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>, <examples.exampleitems.Circle object at 0x...>]
    >>> undo()
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>]
    >>> child in canvas.get_all_items()
    False

Now redo the previous undo action:

    >>> undo_list[:] = redo_list[:]
    >>> undo()
    >>> canvas.get_parent(child) is item
    True
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>, <examples.exampleitems.Circle object at 0x...>]

Remove also works when items are removed recursively (an item and it's
children):

    >>> child = Circle()
    >>> canvas.add(child, parent=item)
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>, <examples.exampleitems.Circle object at 0x...>]
    >>> del undo_list[:]
    >>> canvas.remove(item)
    >>> list(canvas.get_all_items())
    []
    >>> undo()
    >>> list(canvas.get_all_items())                    # doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>, <examples.exampleitems.Circle object at 0x...>]
    >>> canvas.get_children(item)			# doctest: +ELLIPSIS
    [<examples.exampleitems.Circle object at 0x...>]

As well as the reparent() method:

    >>> canvas = Canvas()
    >>> class NameItem:
    ...     def __init__(self, name):
    ...         super(NameItem, self).__init__()
    ...         self.name = name
    ...     def handles(self): return []
    ...     def ports(self): return []
    ...     def point(self, x, y): return 0
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
    >>> list(canvas.get_all_items())
    [<a>, <c>, <d>, <b>]
    >>> del undo_list[:]
    >>> canvas.reparent(ni3, parent=ni2)
    >>> list(canvas.get_all_items())
    [<a>, <b>, <c>, <d>]
    >>> len(undo_list)
    1
    >>> undo()
    >>> list(canvas.get_all_items())
    [<a>, <c>, <d>, <b>]

Redo should work too:

    >>> undo_list[:] = redo_list[:]
    >>> undo()
    >>> list(canvas.get_all_items())
    [<a>, <b>, <c>, <d>]


Undo/redo a connection: see gaphas/tests/test_undo.py


connector.py: Handle
--------------------
Changing the Handle's position is reversible:

    >>> from gaphas import Handle
    >>> handle = Handle()
    >>> handle.pos = 10, 12
    >>> handle.pos
    <Position object on (Variable(10, 20), Variable(12, 20))>
    >>> undo()
    >>> handle.pos
    <Position object on (Variable(0, 20), Variable(0, 20))>

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
    >>> from gaphas.connections import Connections
    >>> e = Element(Connections())
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

item.py: Line
-------------

A line has the following properties: ``line_width``, ``fuzziness``,
``orthogonal`` and ``horizontal``. Each one of then is observed for changes:

    >>> from gaphas import Line
    >>> from gaphas.segment import Segment
    >>> l = Line(Connections())

Let's first add a segment to the line, to test orthogonal lines as well.

    >>> segment = Segment(l, canvas)
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
    [<Handle object on (Variable(0, 20), Variable(0, 20))>, <Handle object on (Variable(10, 20), Variable(10, 20))>]

This is our basis for further testing.

    >>> del undo_list[:]

    >>> Segment(l, canvas).split_segment(0)      # doctest: +ELLIPSIS
    ([<Handle object on (Variable(5, 10), Variable(5, 10))>], [<gaphas.connector.LinePort object at 0x...>])
    >>> l.handles()
    [<Handle object on (Variable(0, 20), Variable(0, 20))>, <Handle object on (Variable(5, 10), Variable(5, 10))>, <Handle object on (Variable(10, 20), Variable(10, 20))>]

The opposite operation is performed with the merge_segment() method:

    >>> undo()
    >>> l.handles()
    [<Handle object on (Variable(0, 20), Variable(0, 20))>, <Handle object on (Variable(10, 20), Variable(10, 20))>]

Also creation and removal of connected lines is recorded and can be undone:

    >>> canvas = Canvas()
    >>> def real_connect(hitem, handle, item):
    ...     def real_disconnect():
    ...         pass
    ...     canvas.connections.connect_item(hitem, handle, item, port=None, constraint=None, callback=real_disconnect)
    >>> b0 = Circle()
    >>> canvas.add(b0)
    >>> b1 = Circle()
    >>> canvas.add(b1)
    >>> l = Line(Connections())
    >>> canvas.add(l)
    >>> real_connect(l, l.handles()[0], b0)
    >>> real_connect(l, l.handles()[1], b1)
    >>> canvas.connections.get_connection(l.handles()[0])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)
    >>> canvas.connections.get_connection(l.handles()[1])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)

Clear already collected undo data:

    >>> del undo_list[:]

Now remove the line from the canvas:

    >>> canvas.remove(l)

The handles are disconnected:

    >>> canvas.connections.get_connection(l.handles()[0])
    >>> canvas.connections.get_connection(l.handles()[1])

Undoing the remove() action should put everything back in place again:

    >>> undo()

    >>> canvas.connections.get_connection(l.handles()[0])      # doctest: +ELLIPSIS
    Connection(item=<gaphas.item.Line object at 0x...>)
    >>> canvas.connections.get_connection(l.handles()[1])      # doctest: +ELLIPSIS
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