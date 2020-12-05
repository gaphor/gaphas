Gaphas 3 Documentation
====================

.. important:: This documentation is in the process of being updated for Gaphas 3.0.


Gaphas is the diagramming widget library for Python.

Gaphas has been built with extensibility in mind. It can be used for many
drawing purposes, including vector drawing applications, and diagram drawing tools.


The basic idea is:

- Gaphas has a Model-View-Controller_ design.
- A model is presented as a protocol in Gaphas. This means that it's very easy to define a class that acts as a model.
- A model can be visualized by one or more Views.
- A constraint solver is used to maintain item constraints and inter-item
  constraints.
- The item (and user) should not be bothered with things like bounding-box
  calculations.
- Very modular: The view contains the basic features. Painters and tools can be swapped out as needed.
- Rendering using Cairo_. This implies the diagrams can be exported in a number
  of formats, including PNG and SVG.

Gaphas is released under the terms of the Apache Software License, version 2.0.

* Git repository: https://github.com/gaphor/gaphas
* Python Package index (PyPI): https://pypi.org/project/gaphas

Table of Contents
=================

.. toctree::
   :caption: The basics
   :maxdepth: 1

   diagram
   tools
   connectors
   solver
   state

.. toctree::
   :caption: Advanced
   :maxdepth: 1

   guide
   segment

.. toctree::
   :caption: API
   :maxdepth: 2

   api

.. toctree::
   :caption: Internals
   :maxdepth: 1

   quadtree
   table
   tree

.. _Cairo: https://cairographics.org
.. _Model-View-Controller: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller
