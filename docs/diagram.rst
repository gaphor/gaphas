Class diagram
=============

This class diagram describes the basic layout of Gaphas.

.. image:: gaphas-canvas.png
   :width: 700

One-oh-one:

:doc:`api/canvas`
   The main canvas class (container for Items)
:doc:`api/items`
   Objects placed on a Canvas. Items can draw themselves, but not act on user events
:doc:`api/solver`
   A constraint solver. Nice to have when you want to connect items together in a generic way.
:doc:`api/gtkview`
   A view to be used in GTK+ applications. This view class is interactive. Interaction with users is handled by Tools.
:doc:`api/painters`
   Painters are the workers when it comes to painting items.
:doc:`api/tools`
   Tools are used to handle user events (such as mouse movement and button presses).
:doc:`api/aspects`
   Tools do not modify the items directly. They use aspects (not the AOP kind) as intermediate step. Since aspects are defined as generic functions, the behaviour for each diagram item type can be slightly different.

Tools
-----

Several tools_ are used to make the overall user experience complete.

.. _tools: tools.html
