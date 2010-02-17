
import unittest
from gaphas import state

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


from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Line
from gaphas.aspect import Connector, ConnectionSink


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
        self.assertEquals(6, len(canvas.solver.constraints))

        canvas.add(b2)
        self.assertEquals(12, len(canvas.solver.constraints))
        
        canvas.add(line)

        sink = ConnectionSink(b1, b1.ports()[0])
        connector = Connector(line, line.handles()[0])
        connector.connect(sink)

        sink = ConnectionSink(b2, b2.ports()[0])
        connector = Connector(line, line.handles()[-1])
        connector.connect(sink)

        self.assertEquals(14, len(canvas.solver.constraints))
        self.assertEquals(2, len(list(canvas.get_connections(item=line))))
        
        del undo_list[:]

        # Here disconnect is not invoked!
        canvas.remove(b2)

        self.assertEquals(7, len(canvas.solver.constraints))
        self.assertEquals(1, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEquals(None, cinfo)

        self.assertEquals([], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x)))
        self.assertEquals([], list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y)))

        undo()

        self.assertEquals(14, len(canvas.solver.constraints))
        self.assertEquals(2, len(list(canvas.get_connections(item=line))))

        cinfo = canvas.get_connection(line.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(line.handles()[-1])
        self.assertEquals(b2, cinfo.connected)

#        self.assertEquals(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.x)))
#        self.assertTrue(list(canvas.solver.constraints_with_variable(line.handles()[-1].pos.y)))
        
if __name__ == '__main__':
    unittest.main()
# vim:sw=4:et:ai
