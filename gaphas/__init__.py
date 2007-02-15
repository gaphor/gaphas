"""
Gaphas 
======

Gaphor's Canvas.

This module contains the application independant parts of Gaphor's Canvas.
It can and may be used by others under the terms of the GNU LGPL licence.
"""

__version__ = "$Revision$"
# $HeadURL$

from canvas import Canvas
from item import Item, Line, Element, Handle
from view import View, GtkView

