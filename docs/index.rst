Gaphas Documentation
====================

Gaphas is the diagramming widget library for Python.

Gaphas has been built with some extensibility in mind. It can be used for many
drawing purposes, including vector drawing applications, diagram drawing tools
and we even have a geographical map demo in our repository.

The basic idea is:

- Items (canvas items) can be added to a Canvas.
- A Canvas can be visualized by one or more Views.
- The canvas maintains the tree structure (parent-child relationships between
  items).
- A constraint solver is used to maintain item constraints and inter-item
  constraints.
- The item (and user) should not be bothered with things like bounding-box
  calculations.
- Very modular: e.g. handle support could be swapped in and swapped out.
- Rendering using Cairo_. This implies the diagrams can be exported in a number
  of formats, including PNG and SVG.

Gaphas is released under the terms of the Apache Software License, version 2.0.

Gaphas has been build using `setuptools` and can be installed as Python Egg.

* Git repository: https://github.com/gaphor/gaphas
* Python Package index (PyPI): https://pypi.org/project/gaphas

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   diagram
   tools
   ports
   state
   undo
   quadtree
   solver
   api


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Cairo: https://cairographics.org
