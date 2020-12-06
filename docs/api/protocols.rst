
Protocols
=========

Although ``gaphas.Canvas`` can be used as a default model, any class that adhere's to the Model protocol can be used as a model.

.. autoclass:: gaphas.view.model.Model
   :members:

An item should implement these methods, so it can be rendered by the View. Not that painters or tools can require additional methods.

.. autoclass:: gaphas.item.Item
   :members:

The view should support just thise one protocol, which will allow update requests to
propagate to the view:

.. automethod:: gaphas.view.model.View.request_update
