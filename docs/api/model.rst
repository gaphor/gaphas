
Model
=====

Protocols
---------

Although ``gaphas.Canvas`` can be used as a default model, any class that adhere's to the Model protocol can be used as a model.

.. autoclass:: gaphas.view.model.Model
   :members:

An item should implement these methods, so it can be rendered by the View. Not that painters or tools can require additional methods.

.. autoclass:: gaphas.item.Item
   :members:

Default implementations
-----------------------

Canvas
~~~~~~

The default implementation for a ``Model``, is a class called ``Canvas``.

.. autoclass:: gaphas.canvas.Canvas
   :members:

Items
~~~~~

Gaphas provides two default items, an box-like element and a line shape.

.. autoclass:: gaphas.item.Element
   :members:

.. autoclass:: gaphas.item.Line
   :members:
