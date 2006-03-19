Gaphor Canvas
=============

This module contains an attempt to a new canvas implementation for Gaphor.

The basic idea is:

 - Items (canvas items) should be used as "adapter" for model elements.
   (not a real adapter since they are statefull).
 - The canvas determines the tree structure (which items are children
   of some other item is maintained by the canvas itself).
 - of course the constrint solver is present.
 - more modular: e.g. handle support could be swapped in and swapped out.
 - rendering using Cairo.


Status
======
tree.py:
	Central tree structure (no more CanvasGroupable)
solver.py:
	A constraint solver (infinite domain, based on diacanvas2's solver)
constraint.py:
	Constraint implementation.


