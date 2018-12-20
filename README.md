# Gaphas
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Build state](https://travis-ci.com/gaphor/gaphas.svg?branch=master)](https://travis-ci.com/gaphor/gaphas)
[![Coverage](https://coveralls.io/repos/github/gaphor/gaphas/badge.svg?branch=master)](https://coveralls.io/github/gaphor/gaphas?branch=master)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Gaphor/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

> Gaphas is the diagramming widget library for Python.

Gaphas is a library that provides the user interface component (widget) for
drawing diagrams. Diagrams can be drawn to screen and then easily exported to a
variety of formats, including SVG and PDF. Want to build an app with chart-like
diagrams? Then Gaphas is for you! Use this library to build a tree, network,
flowchart, or other diagrams.

This library is currently being used by
[Gaphor](https://github.com/gaphor/gaphor) for UML drawing, and
[RAFCON](https://github.com/DLR-RM/RAFCON) for state-machine based robot control.

## :bookmark_tabs: Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [API](#api)
- [Contributing](#contributing)
- [License](#license)

## :scroll: Background

Gaphas was built to provide the foundational diagramming portions of
[Gaphor](https://github.com/gaphor/gaphor). Since Gaphor is built on GTK+ and
cairo, [PyGObject](https://pygobject.readthedocs.io/) provides access to the
GUI toolkit, and [PyCairo](https://pycairo.readthedocs.io/) to the 2D graphics
library. However, there wasn't a project that abstracted these technologies to
easily create a diagramming tool.

Here is how it works:
- Items (canvas items) can be added to a Canvas.
- The canvas maintains the tree structure (parent-child relationships between
  items).
- A constraint solver is used to maintain item constraints and inter-item
  constraints.
- The item (and user) should not be bothered with things like bounding-box
  calculations.
- Very modular: e.g. handle support could be swapped in and swapped out.
- Rendering using Cairo.

The main portions of the library include:
 - canvas - The main canvas class (container for Items).
 - items - Objects placed on a Canvas.
 - solver - A constraint solver to define the layout and connection of items.
 - view - Responsible for the calculation of bounding boxes which is stored in a quadtree data structure for fast access.
 - gtkview - A view to be used in GTK+ applications that interacts with users with tools.
 - painters - The workers used to paint items.
 - tools - Tools are used to handle user events (such as mouse movement and button presses).
 - aspects - Provides an intermediate step between tools and items.

## :floppy_disk: Install

To install Gaphas, simply use pip:

``` {.sourceCode .bash}
$ pip install gaphas
```

Use of a
[virtual environment](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments)
is highly recommended.

## :flashlight: Usage

```python
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gaphas import Canvas, GtkView
from gaphas.examples import Box
from gaphas.painter import DefaultPainter
from gaphas.item import Line
from gaphas.segment import Segment


def create_canvas(canvas, title):
    # Setup drawing window
    view = GtkView()
    view.painter = DefaultPainter()
    view.canvas = canvas
    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(400, 400)
    win_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    window.add(win_box)
    win_box.pack_start(view, True, True, 0)

    # Draw first gaphas box
    b1 = Box(60, 60)
    b1.matrix = (1.0, 0.0, 0.0, 1, 10, 10)
    canvas.add(b1)

    # Draw second gaphas box
    b2 = Box(60, 60)
    b2.min_width = 40
    b2.min_height = 50
    b2.matrix.translate(170, 170)
    canvas.add(b2)

    # Draw gaphas line
    line = Line()
    line.matrix.translate(100, 60)
    canvas.add(line)
    line.handles()[1].pos = (30, 30)
    segment = Segment(line, view=None)
    segment.split_segment(0)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)


c = Canvas()
create_canvas(c, "Simple Gaphas App")
Gtk.main()
```

###  Overview 

The Canvas class (from canvas.py) acts as a container for Item's (from item.py).
The item's parent/child relationships are maintained here (not in the Item!).

An Item can have a set of Handles (from connector.py) which can be used to
manipulate the item (although this is not necessary). Each item has its own
coordinate system with a x and y position, for example a (0, 0) point.
Item.matrix is the transformation relative to the parent item of the Item, as
defined in the Canvas.

Handles can connect to Ports. A Port is a location (line or point) where a
handle is allowed to connect on another item. The process of connecting
depends on the case at hand, but most often involves the creation of some
sort of constraint between the Handle and the item it is connecting to (see
doc/ports.txt).

The Canvas also contains a constraint Solver (from solver.py) that can be used
to solve mathematical dependencies between items (such as Handles that should
be aligned). The constraint solver can also be used to keep constraints
contained within the item true, for example to make sure a box maintains its
rectangular shape.

View (from view.py) is used to visualize a canvas. On a View, a Tool (from
tool.py) can be applied, which will handle user input like button and key
presses. Painters (from painter.py) are used to do the actual drawing. This
module also makes it easy to draw to other media other than a screen, such as a
printer or PDF document.

### Updating item state

If an items needs updating, it sends out an update request on the Canvas
(Canvas.request_update()). The canvas performs an update by performing the
following steps:

1. Pre-update using Item.pre_update(context) for each item marked for update.
2. Update the Canvas-to-Item matrices, for fast transformation of coordinates
   from the canvas' to the items' coordinate system.
   The c2i matrix is stored on the Item as Item._matrix_c2i.
3. Solve the constraints.
4. Normalize the items by setting the coordinates of the first handle to (0, 0).
5. Update the Canvas-to-Item matrices for items that have been changed by
   normalization.
6. Post-update using Item.post_update(context) for each item marked for update,
   including items that have been marked during the constraint solving step.

Gaphas attempts to do as much updating as possible in the {pre|post}_update()
methods, since they are called when the application is not handling user input.

The context contains a CairoContext. This can be used, for example, to
calculate the dimensions of text. One thing to keep in mind is that updating is
done from the canvas. Items should not update sub-items. After the update steps
are complete, the Item should be ready to be drawn.

### Constraint solving

Constraint solving is one of the big features of this library. The Solver is
able to mathematically solve these constraint rules that are applied to an item
or between items. Constraints are applied to items through Variables owned by
the item. An example of applying a constraint to an item is that Element items
use constraints to maintain their rectangular shape. An example of applying
constraints between items is to apply a constraint between a line and a box in
order to connect them.

Constraints that apply to one item are pretty straight forward, as all
variables live in the same coordinate system of the item. The variables, like
the Handle's x and y coordinate can simply be put in a constraint.

When two items are connected to each other and constraints are created, a
problem shows up: variables live in separate coordinate systems. In order to
overcome this problem, a Projection (from solver.py) has been defined. With a
Projection instance, a variable can be "projected" on another coordinate
system. In this case, the Canvas' coordinate system is used when two items are
connected to each other.

### Drawing

Drawing is done by the View. All items marked for redraw, the items that have
been updated, will be drawn in the order in which they reside in the Canvas.
The order starts with the first root item, then its children, then second root
item, etc.

The view context passed to the Items draw() method has the following properties:

 - view - The view we're drawing to.
 - cairo - The CairoContext to draw to.
 - selected - True if the item is actually selected in the view.
 - focused - True if the item has the focus
 - hovered - True if the mouse pointer if over the item. Only the top-most item
             is marked as hovered.
 - dropzone - The item is marked as the drop zone. This happens then an item is
              dragged over the item, and if it is dropped, it will become a
              child of this item.
 - draw_all - True if everything drawable on the item should be drawn, for
              example when calculating the bounding boxes of an item.

The View automatically calculates the bounding box for the item, based on the
items drawn in the draw(context) function (this is only done when really
necessary, e.g. after an update of the item). The bounding box is in viewport
coordinates.

The actual drawing is done by Painters (painter.py). A series of Painters have
been defined: one for handles, one for items, etc.

### Tools

Behaviour is added to the canvas(-view) by tools. Tools can be chained together
in order to provide more complex behaviour.

To make it easy, a DefaultTool has been defined which is a ToolChain instance
with the tools added as follows:

- ToolChain - Delegates to a set of individual tools and keeps track of which
tool has grabbed the focus. This normally happens when the user presses a mouse
button. Once this happens, the tool requests a "grab" and all events, like
motion or button release, are sent directly to the focused tool.

- HoverTool - Makes the item under the mouse button the "hovered item". When
such an item is drawn, its context.hovered_item flag will be set to True.

- HandleTool - Allows for handles to be dragged around and focuses the item
when its handle is clicked on.

- ItemTool - Selects items and enables dragging items around.

- TextEditTool - A demo tool that features a text edit pop-up.

- RubberbandTool - Invoked when the mouse button is pressed on a section of the
view where no items or handles are present. It allows the user to select items
using a "rubber band" selection box.

### Interaction

Interaction with the canvas view (visual component) is handled by tools.
Although the default tools do a fair amount of work, in most cases you'll
desire to create some custom connection behavior. In order to implement these,
HandleTool provides hooks including connect, disconnect and glue.

One of the challenges you'll likely face is what to do when an item is removed
from the canvas and there are other items (lines) connected to it. Gaphas
provides a solution to this by providing a disconnect handler to the handle
instance once it is connected. A function can be assigned to this disconnect
handler, which is then called when the item it is connected to is removed from
the canvas.

### Undo

Gaphas has a simple built-in system for registering changes in its classes and
notifying the application. This code resides in state.py.

There is also a "reverter" framework in place. This system is notified when
objects change their state, and it will figure out the reverse operation that
has to be applied in order to undo the operation.

## :mag: API

The API can be separated into a
[Model-View-Controller](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)
with these three parts:
1. The Model, including the canvas and items
2. The View, called view
3. The Controller, called tools

### Canvas and Items

#### Class: `gaphas.canvas.Canvas`
The `Canvas` is a container for items.
```python
canvas = Canvas()
```

#### Class: `gaphas.item.Item` 
Base class (or interface) for items on a `Canvas`.
```python
item = Item()
```

##### Properties:

 - `matrix`: The item's transformation matrix
 - `canvas`: The canvas, which owns an item
 - `constraints`: list of item constraints, automatically registered
   when the item is added to a canvas; may be extended in subclasses

#### Class: `gaphas.connector.Handle`

Handles are used to support modifications of Items.

If the handle is connected to an item, the `connected_to`
property should refer to the item. A `disconnect` handler should
be provided that handles the required disconnect behaviour, for example
cleaning up the constraints and `connected_to`.

 - pos (`gaphas.connector.Position`): The position of the item, default value is (0, 0).
 - strength (int): The strength of the handle to use in the constraint solver,
 default value is NORMAL, which is 20.
 - connectable (bool): Makes the handle connectable to other items, default value is False.
 - movable (bool): Makes the handle moveable, default value is True.
```python
handle = Handle((10, 10), connectable=True)
```

#### Class: `gaphas.connector.LinePort`

The Line Port is part of an item that provides a line between two handles.

- start (`gaphas.connector.Position`): The start position of the line.
- end (`gaphas.connector.Position`): The end position of the line.

```python
p1, p2 = (0.0, 0.0), (100.0, 100.0)
port = LinePort(p1, p2)
```

#### Class: `gaphas.connector.PointPort`

The Point Port connects the handle to an item using a port at the location of
the handle.
```python
h = Handle((10, 10))
port = PointPort(h.pos)
```

#### Class: `gaphas.solver.Solver`

A Solver solves constraints.

```python
a, b, c = Variable(1.0), Variable(2.0), Variable(3.0)
solver = Solver()
c_eq = EquationConstraint(lambda a,b: a+b, a=a, b=b)
solver.add_constraint(c_eq)
```

#### Class: `gaphas.constraint.EqualsConstraint`
Make 'a' and 'b' equal.

```python
a, b = Variable(1.0), Variable(2.0)
eq = EqualsConstraint(a, b)
eq.solve_for(a)
```
#### Class: `gaphas.constraint.LessThanConstraint`
Ensure one variable stays smaller than another.

```python
a, b = Variable(3.0), Variable(2.0)
lt = LessThanConstraint(smaller=a, bigger=b)
lt.solve_for(a)
```

#### Class: `gaphas.constraint.CenterConstraint`
Ensures a Variable is kept between two other variables.

```python
a, b, center = Variable(1.0), Variable(3.0), Variable()
eq = CenterConstraint(a, b, center)
eq.solve_for(a)
```

#### Class: `gaphas.constraint.EquationConstraint`
Solve a linear equation.

```python
a, b, c = Variable(), Variable(4), Variable(5)
cons = EquationConstraint(lambda a, b, c: a + b - c, a=a, b=b, c=c)
cons.solve_for(a)
```

#### Class: `gaphas.constraint.BalanceConstraint`
Keeps three variables in line, maintaining a specific ratio.

```python
a, b, c = Variable(2.0), Variable(3.0), Variable(2.3, WEAK)
bc = BalanceConstraint(band=(a,b), v=c)
c.value = 2.4
```

#### Class: `gaphas.constraint.LineConstraint`
Solves the equation where a line is connected to a line or side at
a specific point.

```python
line = (Variable(0), Variable(0)), (Variable(30), Variable(20))
point = (Variable(15), Variable(4))
lc = LineConstraint(line=line, point=point)
```

### View

#### Class: `gaphas.view.View`

View class for `gaphas.canvas.Canvas` objects.

```python
canvas = Canvas()
view = View(canvas=canvas)
```

#### Class: `gaphas.view.GtkView`

GTK+ widget for rendering a `gaphas.canvas.Canvas` to a screen.
```python
canvas = Canvas()
win = Gtk.Window()
view = GtkView(canvas=canvas)
win.add(view)
```

#### Class: `gaphas.painter.PainterChain`

Chain up a set of painters.

#### Class: `gaphas.painter.DrawContext`

Special context for drawing the item. It contains a cairo context and
properties like selected and focused.

#### Class: `gaphas.painter.ItemPainter`

Painter to draw an item.

#### Class: `gaphas.painter.CairoBoundingBoxContext`

It is used intercept `stroke()`, `fill()`, and others context operations so
that the bounding box of the item involved can be calculated.

#### Class: `gaphas.painter.BoundingBoxPainter`

A type of ItemPainter which is used to calculate the bounding boxes (in canvas
coordinates) for the items.

#### Class: `gaphas.painter.HandlePainter`

Draw handles of items that are marked as selected in the view.

#### Class: `gaphas.painter.ToolPainter`

Allows the Tool defined on a view to conduct drawing.

#### Class: `gaphas.painter.FocusedItemPainter`

Used to draw on top of all the other layers for the focused item.

### Tools

Interacting with the canvas is done through tools. Tools tell _what_ has to be
done (like moving). To make an element move aspects are defined. Aspects tell
_how_ the behaviour has to be performed.

#### Class: `gaphas.tools.HoverTool`

Makes the item under the mouse cursor the hovered item.

#### Class: `gaphas.tools.ItemTool`

Does selection and dragging of items.

#### Class: `gaphas.tools.HandleTool`

Tool to move handles around.

#### Class: `gaphas.tools.RubberbandTool`

Allows the user to drag a "rubber band" for selecting items in an area. 

#### Class: `gaphas.tools.PanTool`

Captures drag events with the middle mouse button and uses them to translate
the canvas within the view.

#### Class: `gaphas.tools.ZoomTool`

Tool for zooming using two different user inputs: 

- Ctrl + middle-mouse dragging in the up and down direction
- Ctrl + mouse-wheel

#### Class: `gaphas.tools.PlacementTool`

Tool for placing items on the canvas.

   api/aspects

### Extended behaviour

By importing the following modules, extra behaviour is added to the default
view behaviour.


   api/segment
   api/guide

### Miscellaneous

   api/tree
   api/matrix
   api/table
   api/quadtree
   api/geometry
   api/decorators

## :heart: Contributing

1.  Check for open issues or open a fresh issue to start a discussion
    around a feature idea or a bug. There is a 
    [first-timers-only](https://github.com/gaphor/gaphor/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Afirst-timers-only)
    tag for issues that should be ideal for people who are not very
    familiar with the codebase yet.
2.  Fork [the repository](https://github.com/gaphor/gaphas) on
    GitHub to start making your changes to the **master** branch (or
    branch off of it).
3.  Write a test which shows that the bug was fixed or that the feature
    works as expected.
4.  Send a pull request and bug the maintainers until it gets merged and
    published. :smile: Make sure to add yourself to
    [AUTHORS](https://github.com/gaphor/gaphas/blob/master/AUTHORS.md).

See [the contributing file](CONTRIBUTING.md)!


## :copyright: License
Copyright (C) Arjan Molenaar and Dan Yeaw

Licensed under the [Apache License 2.0](LICENSE).


## Contributors

Thanks goes to these wonderful people ([emoji key](https://github.com/kentcdodds/all-contributors#emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore -->
| [<img src="https://avatars0.githubusercontent.com/u/96249?v=4" width="100px;"/><br /><sub><b>Arjan Molenaar</b></sub>](https://github.com/amolenaar)<br />[💻](https://github.com/danyeaw/gaphas/commits?author=amolenaar "Code") [🐛](https://github.com/danyeaw/gaphas/issues?q=author%3Aamolenaar "Bug reports") [📖](https://github.com/danyeaw/gaphas/commits?author=amolenaar "Documentation") [👀](#review-amolenaar "Reviewed Pull Requests") [💬](#question-amolenaar "Answering Questions") [🔌](#plugin-amolenaar "Plugin/utility libraries") | [<img src="https://avatars1.githubusercontent.com/u/10014976?v=4" width="100px;"/><br /><sub><b>Dan Yeaw</b></sub>](https://ghuser.io/danyeaw)<br />[💻](https://github.com/danyeaw/gaphas/commits?author=danyeaw "Code") [⚠️](https://github.com/danyeaw/gaphas/commits?author=danyeaw "Tests") [👀](#review-danyeaw "Reviewed Pull Requests") [🐛](https://github.com/danyeaw/gaphas/issues?q=author%3Adanyeaw "Bug reports") [💬](#question-danyeaw "Answering Questions") [🚇](#infra-danyeaw "Infrastructure (Hosting, Build-Tools, etc)") [📖](https://github.com/danyeaw/gaphas/commits?author=danyeaw "Documentation") | [<img src="https://avatars2.githubusercontent.com/u/105664?v=4" width="100px;"/><br /><sub><b>wrobell</b></sub>](https://github.com/wrobell)<br />[💻](https://github.com/danyeaw/gaphas/commits?author=wrobell "Code") [⚠️](https://github.com/danyeaw/gaphas/commits?author=wrobell "Tests") | [<img src="https://avatars3.githubusercontent.com/u/890576?v=4" width="100px;"/><br /><sub><b>Jean-Luc Stevens</b></sub>](https://github.com/jlstevens)<br />[💻](https://github.com/danyeaw/gaphas/commits?author=jlstevens "Code") [🐛](https://github.com/danyeaw/gaphas/issues?q=author%3Ajlstevens "Bug reports") [📖](https://github.com/danyeaw/gaphas/commits?author=jlstevens "Documentation") |
| :---: | :---: | :---: | :---: |
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/kentcdodds/all-contributors) specification. Contributions of any kind welcome!