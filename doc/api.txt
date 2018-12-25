#############
API reference
#############

This part describes the API of Gaphas.

The API can be separated into three parts. First of all there's the model
(canvas and items). Then there's the view (view) and controllers (tools).

Some more generic stuff is also described here.

Canvas and items
----------------

.. toctree::
   :maxdepth: 2

   api/canvas
   api/items
   api/connectors
   api/solver  
   api/constraints  
   api/utils


View and tools
--------------

Everything related to displaying the canvas and interacting with it.

.. toctree::
   :maxdepth: 2

   api/view
   api/gtkview
   api/painters

Interacting with the canvas is done through tools. Tools tell _what_ has to be done (like moving). To make an element move aspects are defined. Aspects tell _how_ the behaviour has to be performed.

.. toctree::
   :maxdepth: 2

   api/tools
   api/aspects

Extended behaviour
~~~~~~~~~~~~~~~~~~

By importing the following modules, extra behaviour is added to the default
view behaviour.

.. toctree::
   :maxdepth: 2

   api/segment
   api/guide

Miscellaneous
-------------

.. toctree::
   :maxdepth: 2

   api/tree
   api/matrix
   api/table
   api/quadtree
   api/geometry
   api/decorators

