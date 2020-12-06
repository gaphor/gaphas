Class diagram
=============

This class diagram describes the basic layout of Gaphas.

.. image:: gaphas-canvas.png
   :width: 700

The central class is ``GtkView``. It takes a model.
A default implementation is provided by `gaphas.Canvas`.
A view is rendered by ``Painter``s. Interaction is handled
by ``Tool``s.
