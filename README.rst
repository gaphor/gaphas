Gaphor's Canvas
===============

This module contains a new canvas implementation for Gaphor.

Homepage: http://github.com/amolenaar/gaphas

Issue tracker: http://gaphor.lighthouseapp.com

Mailing list: gaphor-dev@googlegroups.com


The basic idea is:

- Items (canvas items) can be added to a Canvas.
- The canvas maintains the tree structure (parent-child relationships between
  items).
- A constraint solver is used to maintain item constraints and inter-item
  constraints.
- The item (and user) should not be bothered with things like bounding-box
  calculations.
- Very modular: e.g. handle support could be swapped in and swapped out.
- Rendering using Cairo.

 Gaphas is released under the terms of the GNU Library General Public License
 (LGPL). See the COPYING file for details.

.. contents::


How it Works
============

The Canvas class (from canvas.py) acts as a container for Item's (from item.py).
The item's parent/child relationships are maintained here (not in the Item!).

An Item can have a set of Handle's (from connector.py) which can be used to
manipulate the item (although this is not necessary). Each item has it's own
coordinate system (a (0, 0) point). Item.matrix is the transformation
relative to the parent item of the Item, as defined in the Canvas.
Handles can connect to Ports. A Port is a location (line or point) where a
handle is allowed to connect on another item. The process of connecting
depends on the case at hand, but most often involves the creation of some
sort of constraint between the Handle and the item it's connecting to (see
doc/ports.txt).

The Canvas also contains a constraint Solver (from solver.py) that can be used
to solve mathematical dependencies between items (such as Handles that should
be aligned). The constraint solver is also a handy tool to keep constraint
in the item true (e.g. make sure a box maintains it's rectangular shape).

View (from view.py) is used to visualize a canvas. On a View, a Tool
(from tool.py) can be applied, which will handle user input (button presses,
key presses, etc.). Painters (from painter.py) are used to do the actual
drawing. This way it should be easy do draw to other media than the screen,
such as a printer or PDF document.

Updating item state
-------------------
If an items needs updating, it sets out an update request on the Canvas
(Canvas.request_update()). The canvas performs an update by calling:

1. Item.pre_update(context) for each item marked for update
2. Updating Canvas-to-Item matrices, for fast transformation of coordinates
   from the canvas' to the items' coordinate system.
   The c2i matrix is stored on the Item as Item._matrix_c2i.
3. Solve constraints.
4. Normalize items by setting the coordinates of the first handle to (0, 0).
5. Updating Canvas-to-Item matrices for items that have been changed by
   normalization, just to be on the save side.
6. Item.post_update(context) for each item marked for update, including items
   that have been marked during constraint solving.

The idea is to do as much updating as possible in the {pre|post}_update()
methods, since they are called when the application is not handling user input.

The context contains:

:cairo: a CairoContext, this can be used to calculate the dimensions of text
        for example

NOTE: updating is done from the canvas, items should not update sub-items.

After an update, the Item should be ready to be drawn.

Constraint solving
------------------
A word about the constraint solver seems in place. It is one of the big
features of this library after all. The Solver is able to solve constraints.
Constraints can be applied to items (Variables owned by the item actually).
Element items, for example, uses constraints to maintain their recangular
shape. Constraints can be created *between* items (for example a line that
connects to a box).

Constraints that apply to one item are pretty straight forward, as all variables
live in the same coordinate system (of the item). The variables (in most cases
a Handle's x and y coordinate) can simply be put in a constraint.

When two items are connected to each other and constraints are created, a
problem shows up: variables live in separate coordinate systems. To overcome
this problem a Projection (from solver.py) has been defined. With a Projection
instance, a variable can be "projected" on another coordinate system. In this
case, where two items are connecting to each other, the Canvas' coordinate
system is used.


Drawing
-------
Drawing is done by the View. All items marked for redraw (e.i. the items
that had been updated) will be drawn in the order in which they reside in the
Canvas (first root item, then it's children; second root item, etc.)

The view context passed to the Items draw() method has the following properties:

:view:     the view we're drawing to
:cairo:    the CairoContext to draw to
:selected: True if the item is actually selected in the view
:focused:  True if the item has the focus
:hovered:  True if the mouse pointer if over the item. Only the top-most item
           is marked as hovered.
:dropzone: The item is marked as drop zone. This happens then an item is
           dragged over the item and (if dropped) will become a child of
           this item.
:draw_all: True if everything drawable on the item should be drawn (e.g. when
           calculating the bounding boxes).

The View automatically calculates the bounding box for the item, based on the
items drawn in the draw(context) function (this is only done when really
necessary, e.g. after an update of the item). The bounding box is in viewport
coordinates.

The actual drawing is done by Painters (painter.py). A series of Painters have
been defined: one for handles, one for items, etc.

Tools
-----
Behaviour is added to the canvas(-view) by tools.

Tools can be chained together in order to provide more complex behaviour.

To make it easy a DefaultTool has been defined: a ToolChain instance with the
tools added that are listed in the following sections.

ToolChain
    The ToolChain does not do anything by itself. It delegates to a set of
    tools and keeps track of which tool has grabbed the focus. This happens
    most of the time when the uses presses a mouse button. The tool requests a
    grab() and all upcoming events (e.g. motion or button release events) are
    directly sent to the focused tool.

HoverTool
    A small and simple tool that does nothing more than making the item under
    the mouse button the "hovered item". When such an item is drawn, its
    context.hovered_item flag will be set to True.

HandleTool
    The HandleTool is used to deal with handles. Handles can be dragged around.
    Clicking on a handle automatically makes the underlying item the focused
    item.

ItemTool
    The item tool takes care of selecting items and dragging items around.

TextEditTool
    This is a demo-tool, featuring a text-edit pop-up.

RubberbandTool
    The last tool in line is the rubber band tool. It's invoked when the mouse
    button is pressed on a section of the view where no items or handles are
    present. It allows the user to select items using a selection box
    (rubber band).


Interaction
-----------
Interaction with the canvas view (visual component) is handled by tools.
Although the default tools do a fair amount of work, in most cases you'll
see that especially the way items connect with each other is not the way
you want it. That's okay. HandleTool provides some hooks (connect, disconnect
and glue) to implement custom connection behaviour (in fact, the default
implementation doesn't do any connecting at all!).

One of the problems you'll face is what to do when an item is removed from the
canvas and there are other items (lines) connected to. This problem can be
overcome by providing a disconnect handler to the handle instance ones it is
connected. A callable object (e.g. function) can be assigned to the handle. It
is called at the moment the item it's connected to is removed from the canvas.


Undo
====

Gaphas has a simple build-in system for registering changes in it's classes and
notifying the application. This code resides in state.py.

There is also a "reverter" framework in place. This "framework" is notified
when objects change their state and will figure out the reverse operation that
has to be applied in order to undo the operation.

See state.txt and undo.txt for details and usage examples.


Guidelines
==========

Documentation should be in UK English.

Following the `Python coding guidelines`_ indentation should be 4 spaces
(no tabs), function and method names should be ``lowercase_with_underscore()``.
We're using two white lines as separator between methods, as it makes method
boundries more clear.


.. _Python coding guidelines: http://www.python.org/dev/peps/pep-0008/

