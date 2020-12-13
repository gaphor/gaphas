Painters
========

Painters are used to draw the view.

Protocols
---------

Each painter adheres to the ``Painter`` protocol.

.. autoclass:: gaphas.painter.Painter
   :members:

Some painters, such as ``FreeHandPainter`` and ``BoundingBoxPainter``, require a special painter protocol:

.. autoclass:: gaphas.painter.painter.ItemPainterType
   :members:


Default implementations
-----------------------

.. autoclass:: gaphas.painter.PainterChain
   :members: append, prepend


.. autoclass:: gaphas.painter.ItemPainter

.. autoclass:: gaphas.painter.HandlePainter

.. autoclass:: gaphas.painter.BoundingBoxPainter

.. autoclass:: gaphas.painter.FreeHandPainter


Rubberband tool
---------------

A special painter is used to display rubberband selection. This painter shares some state with
the rubberband tool.

.. autoclass:: gaphas.tool.rubberband.RubberbandPainter