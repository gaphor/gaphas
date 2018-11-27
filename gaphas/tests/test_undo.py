import unittest

from gaphas import state
from gaphas.aspect import Connector, ConnectionSink
from gaphas.canvas import Canvas
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

        canvas = Canvas()
        canvas.add(b1)
        self.assertEqual(2, len(canvas.solver.constraints))

        canvas.add(b2)
        self.assertEqual(4, len(canvas.solver.constraints))

        canvas.add(line)

        sink = ConnectionSink(b1, b1.ports()[0])
        connector = Connector(line, line.handles()[0])
        connector.connect(sink)

        sink = ConnectionSink(b2, b2.ports()[0])
        connector = Connector(line, line.handles()[-1])
        connector.connect(sink)

        self.assertEqual(6, len(canvas.solver.constraints))
        self.assertEqual(2, len(list(canvas.get_connections(item=line))))

        del undo_list[:]

        # Here disconnect is not invoked!
        canvas.remove(b2)

        self.assertEqual(3, len(canvas.solver.constraints))
        self.assertEqual(1, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEqual(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEqual(None, cinfo)

        self.assertEqual(
            [], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x))
        )
        self.assertEqual(
            [], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y))
        )

        undo()

        self.assertEqual(6, len(canvas.solver.constraints))
        self.assertEqual(2, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEqual(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEqual(b2, cinfo.connected)


#        self.assertEqual(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x)))
#        self.assertTrue(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y)))

if __name__ == "__main__":
    unittest.main()
# vim:sw=4:et:ai
