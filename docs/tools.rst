Interacting with diagrams
=========================

Tools are used to handle user actions, like moving a mouse pointer over the
screen and clicking on items in the canvas.

Tools are registered on the ``View``. They have some internal state (e.g. when and
where a mouse button was pressed). Therefore tools can not be reused by
different views [#]_.

Tools are simply `Gtk.EventController` instances.
For a certain action to happen multiple user events are used. For example a
click is a combination of a button press and button release event (only talking
mouse clicks now). In most cases also some movement is done. A sequence of a
button press, some movement and a button release is treated as one transaction.
Once a button is pressed the tool registers itself as the tool that will deal
with all subsequent events (a ``grab``).


Several events can happen based on user events. E.g.:

- item is hovered over (motion)
- item is hovered over while another item is being moved (``press``, ``motion``)
- item is hovered over while dragging something else (DnD; ``press``, ``move``)
- grabbed (button press on item)
- handle is grabbed (button press on handle)
- center of line segment is grabbed (will cause segment to split; button press on line)
- ungrabbed (button release)
- move (item is moved -> hover + grabbed)
- key is pressed
- key is released
- modifier is pressed (e.g. may cause mouse pointer to change, giving a hit
  about what a grab event will do.

There is a lot of behaviour possible and it can depend on the kind of diagrams that are created what has to be done.

To organize the event sequences and keep some order in what the user is doing Tools are used. Tools define what has to happen (find a handle nearly the mouse cursor, move an item).

Gaphas contains a set of default tools. Each tool is meant to deal with a special part of the view. A list of responsibilities is also defined here:

:hover tool:
  First thing a user wants to know is if the mouse cursor is over an item. The ``HoverTool`` makes that explicit.
  - Find a handle or item, if found, mark it as the ``hovered_item``
:item tool:
  Items are the elements that are actually providing any (visual) meaning to the diagram. ItemTool deals with moving them around. The tool makes sure the right subset of selected elements are moved (e.g. you don't want to move a nested item if its parent item is already moved, this gives funny visual effects)

  - On click: find an item, if found become the grabbed tool and set the item as focused. If a used clicked on a handle position that is taken into account
  - On motion: move the selected items (only the ones that have no selected parent items)
  - On release: release grab and release item

  The item tool invokes the `Move` aspect, or the `HandleMove` aspect in case a handle is being grabbed.

:rubberband tool:
  If no handle or item is selected a rubberband selection is started.
:scroll and zoom tool:
  Handy tools for moving the canvas around and zooming in and out. Convenience functionality, basically.

There is one more tool, that has not been mentioned yet:

:placement tool:
  A special tool to use for placing new items on the screen.

As said, tools define *what* has to happen, they don't say how. Take for example finding a handle: on a normal element (a box or something) that would mean find the handle in one of the corners. On a line, however, that may also mean a not-yet existing handle in the middle of a line segment (there is a functionality that splits the line segment).

The *how* is defined by so called aspects [#]_.

Separating the *What* from the *How*
------------------------------------

The *what* is decided in a tool. Based on this the *how* logic can be applied
to the item at hand. For example: if an item is clicked, it should be marked as
the focused item. Same for dragging: if an item is dragged it should be updated
based on the event information. It may even apply this to all other selected
items.

The how logic depends actually on the item it is applied to. Lines have different behaviours than boxes for example. In Gaphas this has been resolved by defining a generic methods. To put it simple: a generic method is a factory that returns a specific method (or instance of a class, as we do in gaphas) based on its parameters.

The advantage is that more complex behaviour can be composed. Since the
decision on what should happen is done in the tool, the aspect which is then
used to work on the item ensures a certain behaviour is performed.

.. [#] as opposed to versions < 0.5, where tools could be shared among multiple views.
.. [#] not the AOP term. The term aspect is coming from a paper by Dirk Riehe: The Tools and Materials metaphor https://wiki.c2.com/?ToolsAndMaterialsMetaphor..>.
