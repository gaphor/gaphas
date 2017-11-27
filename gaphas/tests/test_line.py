#!/usr/bin/env python

# Copyright (C) 2008-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Dan Yeaw <dan@yeaw.me>
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

import unittest

from gaphas import state
from gaphas.itemcontainer import ItemContainer
from gaphas.item import Line
from gaphas.segment import Segment

undo_list = []
redo_list = []


def undo_handler(event):
    undo_list.append(event)


def undo():
    apply_me = list(undo_list)
    del undo_list[:]
    apply_me.reverse()
    for e in apply_me:
        state.saveapply(*e)
    redo_list[:] = undo_list[:]
    del undo_list[:]


class TestCaseBase(unittest.TestCase):
    """
    Abstract test case class with undo support.
    """

    def setUp(self):
        state.observers.add(state.revert_handler)
        state.subscribers.add(undo_handler)

    def tearDown(self):
        state.observers.remove(state.revert_handler)
        state.subscribers.remove(undo_handler)


class LineTestCase(TestCaseBase):
    """
    Basic line item tests.
    """

    def test_initial_ports(self):
        """Test initial ports amount
        """
        line = Line()
        self.assertEquals(1, len(line.ports()))

    def test_orthogonal_horizontal_undo(self):
        """Test orthogonal line constraints bug (#107)
        """
        canvas = ItemContainer()
        line = Line()
        canvas.add(line)
        assert not line.horizontal
        assert len(canvas.solver._constraints) == 0

        segment = Segment(line, None)
        segment.split_segment(0)

        line.orthogonal = True

        self.assertEquals(2, len(canvas.solver._constraints))
        after_ortho = set(canvas.solver._constraints)

        del undo_list[:]
        line.horizontal = True

        self.assertEquals(2, len(canvas.solver._constraints))

        undo()

        self.assertFalse(line.horizontal)
        self.assertEquals(2, len(canvas.solver._constraints))

        line.horizontal = True

        self.assertTrue(line.horizontal)
        self.assertEquals(2, len(canvas.solver._constraints))

    def test_orthogonal_line_undo(self):
        """Test orthogonal line undo
        """
        canvas = ItemContainer()
        line = Line()
        canvas.add(line)

        segment = Segment(line, None)
        segment.split_segment(0)

        # start with no orthogonal constraints
        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        # check orthogonal constraints
        self.assertEquals(2, len(canvas.solver._constraints))
        self.assertEquals(3, len(line.handles()))

        undo()

        self.assertFalse(line.orthogonal)
        self.assertEquals(0, len(canvas.solver._constraints))
        self.assertEquals(2, len(line.handles()))

# vim:sw=4:et
