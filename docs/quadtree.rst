Quadtree
########

In order to find items and handles fast on a 2D surface, a geometric structure is required.

There are two popular variants: Quadtrees_ and R-trees_. R-trees are tough and
well suited for non-moving data. Quadtrees are easier to understand and easier
to maintain.

Idea:

* Divide the view in 4 quadrants and place each item in a quadrant.
* When a quadrant has more than ''x'' elements, divide it again.
* When an item overlaps more than one quadrant, it's added to the owner.

Gaphas uses item bounding boxed to determine where items should be put.

It is also possible to relocate or remove items to the tree.

The Quadtree itself is added as part of Gaphas' View. The view is aware of
item's bounding boxes as it is responsible for user interaction. The Quadtree
is set to the size of the window. As a result items which are part of the
diagram, may be placed outside the window and thus will not be added to the
quadtree. Item's that are partly in- and partly outside the window will be
clipped.

Interface
---------

The Quadtree interface is simple and tailored towards the use cases of
gaphas.

Important properties:

* bounds: boundaries of the canvas/view

Methods for working with items in the quadtree:

* `add(item, bounds)`: add an item to the quadtree
* `remove(item)`: remove item from the tree
* `update(item, new_bounds)`: replace an item in the quadtree, using it's new boundaries.
* Multiple ways of finding items have been implemented:
  1. Find item closest to point
  2. Find all items within distance `d` of a point
  3. Find all items inside a rectangle
  4. Find all items inside or intersecting with a rectangle

Methods working on the quadtree itself:

* `resize(new_bounds)`: stretch the boundaries of the quadtree if necessary.

Implementation
--------------

The implementation of gaphas' Quadtree can be found at https://github.com/gaphor/gaphas/blob/master/gaphas/quadtree.py.

Here's an example of the Quadtree in action (Gaphas' demo app with `gaphas.view.DEBUG_DRAW_QUADTREE` enabled):

.. image:: quadtree.png

The screen is divided into four equal quadrants. The first quadrant has many items, therefore it has been divided again.

References
~~~~~~~~~~

(!PyGame)
http://www.pygame.org/wiki/QuadTree?parent=CookBook

(PythonCAD)
https://sourceforge.net/p/pythoncad/code/ci/master/tree/PythonCAD/Generic/quadtree.py

.. _Quadtrees: http://en.wikipedia.org/wiki/Quadtree
.. _R-trees: http://en.wikipedia.org/wiki/R-tree
