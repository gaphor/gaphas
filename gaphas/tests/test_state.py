#!/usr/bin/env python

# Copyright (C) 2009-2017 Artur Wroblewski <wrobell@pld-linux.org>
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

from __future__ import absolute_import

import unittest

from gaphas.state import reversible_pair, observed, _reverse


class SList(object):
    def __init__(self):
        self.l = list()

    def add(self, node, before=None):
        if before:
            self.l.insert(self.l.index(before), node)
        else:
            self.l.append(node)

    add = observed(add)

    @observed
    def remove(self, node):
        self.l.remove(self.l.index(node))


class StateTestCase(unittest.TestCase):
    def test_adding_pair(self):
        """Test adding reversible pair
        """
        reversible_pair(SList.add, SList.remove,
                        bind1={'before': lambda self, node: self.l[self.l.index(node) + 1]}
                        )

        self.assertTrue(SList.add in _reverse)
        self.assertTrue(SList.remove in _reverse)
