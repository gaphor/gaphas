#!/usr/bin/env python

# Copyright (C) 2010-2017 Arjan Molenaar <gaphor@gmail.com>
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
from gaphas.aspect import Connector, ConnectionSink
from gaphas.itemcontainer import ItemContainer
from gaphas.examples import Box
from gaphas.item import Line

state.observers.clear()
state.subscribers.clear()

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


class UndoTestCase(unittest.TestCase):
    def setUp(self):
        state.observers.add(state.revert_handler)
        state.subscribers.add(undo_handler)

    def shutDown(self):
        state.observers.remove(state.revert_handler)
        state.subscribers.remove(undo_handler)

    def testUndoOnDeletedElement(self):
        b1 = Box()

        b2 = Box()
        line = Line()

        canvas = ItemContainer()
        canvas.add(b1)
        self.assertEquals(2, len(canvas.solver.constraints))

        canvas.add(b2)
        self.assertEquals(4, len(canvas.solver.constraints))

        canvas.add(line)

        sink = ConnectionSink(b1, b1.ports()[0])
        connector = Connector(line, line.handles()[0])
        connector.connect(sink)

        sink = ConnectionSink(b2, b2.ports()[0])
        connector = Connector(line, line.handles()[-1])
        connector.connect(sink)

        self.assertEquals(6, len(canvas.solver.constraints))
        self.assertEquals(2, len(list(canvas.get_connections(item=line))))

        del undo_list[:]

        # Here disconnect is not invoked!
        canvas.remove(b2)

        self.assertEquals(3, len(canvas.solver.constraints))
        self.assertEquals(1, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEquals(None, cinfo)

        self.assertEquals([], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x)))
        self.assertEquals([], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y)))

        undo()

        self.assertEquals(6, len(canvas.solver.constraints))
        self.assertEquals(2, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEquals(b2, cinfo.connected)


# self.assertEquals(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x)))
#        self.assertTrue(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y)))

if __name__ == '__main__':
    unittest.main()
# vim:sw=4:et:ai
