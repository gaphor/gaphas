Class diagram
=============

This class diagram describes the basic layout of Gaphas.

The central class is ``GtkView``. It takes a model.
A default implementation is provided by `gaphas.Canvas`.
A view is rendered by Painters. Interaction is handled
by Tools.

.. diagram:: view
   :align: center

Painting is done by painters. Each painter will paint a layer of the canvas.

.. diagram:: painter
   :align: center

Besides the view, there is constraint based connection management.
Constraints can be used within an item, and to connect different items.

.. diagram:: connections
   :align: center

A default model and item implementations, a line and an element.

.. diagram:: canvas
   :align: center
