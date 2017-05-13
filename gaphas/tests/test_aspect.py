#!/usr/bin/env python

# Copyright (C) 2009-2010 Arjan Molenaar <gaphor@gmail.com>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.
"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.aspect import *
from gaphas.canvas import Canvas
from gaphas.view import View

class AspectTestCase(unittest.TestCase):
    """
    Test aspects for items.
    """

    def setUp(self):
        self.canvas = Canvas()
        self.view = View(self.canvas)


    def test_selection_select(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        selection = Selection(item, view)
        assert item not in view.selected_items
        selection.select()
        assert item in view.selected_items
        assert item is view.focused_item
        selection.unselect()
        assert item not in view.selected_items
        assert None is view.focused_item


    def test_selection_move(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        inmotion = InMotion(item, view)
        self.assertEquals((1, 0, 0, 1, 0, 0), tuple(item.matrix))
        inmotion.start_move((0, 0))
        inmotion.move((12, 26))
        self.assertEquals((1, 0, 0, 1, 12, 26), tuple(item.matrix))


# vim:sw=4:et:ai
