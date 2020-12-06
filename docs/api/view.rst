View
====

Protocols
---------

Although gaphas.Canvas can be used as a default model, any class that adhere's to the Model protocol can be used as a model.

.. autoclass:: gaphas.view.model.Model
   :members:

The view should support just thise one protocol, which will allow update requests to
propagate to the view:

.. automethod:: gaphas.view.model.View.request_update


GtkView
-------
.. autoclass:: gaphas.view.GtkView
   :members: