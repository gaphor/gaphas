Gaphor Canvas
=============

This module contains a new canvas implementation for Gaphor.

The basic idea is:

 - Items (canvas items) should be used as "adapter" for model elements.
   (not a real adapter since they are stateful).
 - The canvas determines the tree structure (which items are children
   of some other item is maintained by the canvas itself).
 - of course the constraint solver is present.
 - more modular: e.g. handle support could be swapped in and swapped out.
 - rendering using Cairo.


To do
=====

This is it as far as stage 1 is concerned. I have implemented:
 v a render cycle.
 v zoom and move functionality (canvas2world).
 v scroll-bars work.
 v a set of tools and a ToolChain (to chain them together).
 v rubberband selection

Stage 2:
 v check the code with pylint for strange things.
 v line item
 v placement tool
 v connection protocol
 v make update cycle independent from render (expose) event.
    This is something we might do if the response is getting bad.
 ? rotating and shearing for Element items.
    Do we need this?

Stage 3:
 v make double and triple click work.
 v text edit tool (gtk.Edit in popup window?)

Stage n:
 - Drop-zone tool
     the idea is that for example you have a Package and when you drag
     a Class into it it automatically makes the Package its owning element.
 v undo management


How it Works
============

The Canvas class (from canvas.py) acts as a container for Item's (from item.py).
The item's parent/child relationships are maintained here (not in the Item!).

An Item can have a set of Handle's (also from item.py) which can be used to
manipulate the item (although this is not necessary). Each item has it's own
coordinate system (a (0, 0) point). Item.matrix is the transformation
relative to the parent item of the Item, as defined in the Canvas.

The Canvas also contains a constraint Solver (from solver.py) that can be used
to solve mathematical dependencies between items (such as Handles that should
be aligned).

View (from view.py) is used to visualize a canvas. On a View, a Tool
(from tool.py) can be assigned, which will handle user input (button presses,
key presses, etc.). Painters (from painter.py) are used to do the actual
drawing. This way it should be easy do draw to other media than the screen,
such as a printer or PDF document.

Updating item state
-------------------
If an items needs updating, it sets out an update request on the Canvas
(Canvas.request_update for a full update or Canvas.request_matrix_update() if
only the transformation matrix has changed). The canvas performs an update by
calling:

 1. Item.pre_update(context)
 2. updating World-to-Item matrices, for fast transformation of coordinates
    from the world to the items' coordinate system.
    The w2i matrix is stored on the Item as Item._matrix_w2i.
 3. solve constraints
 4. updating World-to-Item matrices again, just to be on the save side.
 5. Item.update(context)

The idea is to do as much updating as possible in the (pre_)update() methods,
since they are called when the application is not handling user input.

The context contains:

 parent:   parent item of the item, or None
 children: child items of this item (do not need to force updates for those)
 cairo:    a CairoContext, this can be used to calculate the dimensions of text
           for example

NOTE: updating is done from the canvas, items should not update sub-items.

After an update, the Item should be ready top be drawn.

Drawing
-------
Drawing is done by the View. It calls the draw(context) method for each *root*
item in the canvas. Items should instruct the engine to draw sub-item (children)
by calling context.draw_children().

In addition to draw_children(), the context has the following properties:

 view:     the view we're drawing to
 cairo:    the CairoContext to draw to
 parent:   parent item of the item, or None
 children: child items of this item (do not need to force updates for those)
 selected: True if the item is actually selected in the view
 focused:  True if the item has the focus
 hovered:  True if the mouse pointer if over the item. Only the top-most item
           is marked as hovered.
 draw_all: True if everything drawable on the item should be drawn (e.g. when
           calculating the bounding boxes).

The View automatically calculates the bounding box for the item, based on the
items drawn in the draw(context) function (this is only done once after each
Item.update()). The bounding box is stored on the item as Item._view_bounds
as a geometry.Rectangle object. The bounding box is in viewport coordinates.


Tools
-----
Behavior is added to the canvas(-view) by tools.

Tools can be chained together in order to provide more complex behavior.

DefaultTool
HandleTool
ChainTool (connect behavior of tools)


Interaction
-----------
Interaction with the canvas view (visual component) is handled by tools.
Although the default tools do a fair amount of work, in most cases you'll
see that especially the way items connect with each other is not the way
you want it. That's okay. HandleTool provides some hooks (connect, disconnect and glue) to implement custom connection behavior (in fact, the default implementation doesn't do any connecting at all!).

One of the problems you'll face is what to do when an item is removed from the
canvas and there are other items (lines) connected to. This problem can be
solved by providing a disconnect handler to the handle instance ones it is
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


Files
=====

Canvas independent classes:

tree.py:
	Central tree structure (no more CanvasGroupable)
solver.py:
	A constraint solver (infinite domain, based on diacanvas2's solver)
constraint.py:
	Constraint implementation.
geometry.py:
	Matrix, Rectangle calculations.

Canvas classes:

item.py:
	Canvas item and handle
canvas.py:
	Canvas class
view.py:
	Canvas view (renderer) class
tool.py:
	Base class for Tools (which handle events on the view).

Other:

examples.py:
	Simple example classes.

Guidelines
----------
Following the Python coding guidelines
<http://www.python.org/dev/peps/pep-0008/> indentation should be 4 spaces
(no tabs), function and method names should be lowercase_with_underscore(),
and files should contain a __version__ property, like this:

  __version__ = "$Revision$"
  # $HeadURL$

It should be placed after the module docstring.

This inhibits that for each .py file, the svn:keywords property should be set
to "Revision HeadURL". This can be done manually:

  $ svn propset svn:keywords "Revision HeadURL" myfile.py

or by configuring your ~/.subversion/config file to use auto-props:

  [miscellany]
  # ...
  enable-auto-props = yes

  [auto-props]
  # ...
  *.py = svn:keywords=Revision HeadURL


