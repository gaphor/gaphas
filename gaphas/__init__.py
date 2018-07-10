"""
Gaphas
======

Gaphor's Canvas.

This module contains the application independant parts of Gaphor's
Canvas.  It can and may be used by others under the terms of the GNU
LGPL licence.

Notes
=====

In py-cairo 1.8.0 (or 1.8.1, or 1.8.2) the multiplication order has
been reverted. This causes bugs in Gaphas.

Also a new method ``multiply()`` has been introduced. This method is
used in Gaphas instead of the multiplier (``*``). In both the
``Canvas`` and ``View`` class a workaround is provided in case an
older version of py-cairo is used.
"""
from __future__ import absolute_import

__version__ = "$Revision$"
# $HeadURL$


from .canvas import Canvas
from .connector import Handle
from .item import Item, Line, Element
from .view import View, GtkView

# vi:sw=4:et:ai
