
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
        l = Line()

        canvas = Canvas()
        canvas.add(b1)
        self.assertEquals(6, len(canvas.solver.constraints))

        canvas.add(b2)
        self.assertEquals(12, len(canvas.solver.constraints))
        
        canvas.add(l)

        sink = ConnectionSink(b1, b1.ports()[0])
        connector = Connector(l, l.handles()[0])
        connector.connect(sink)

        sink = ConnectionSink(b2, b2.ports()[0])
        connector = Connector(l, l.handles()[-1])
        connector.connect(sink)

        self.assertEquals(14, len(canvas.solver.constraints))
        
        del undo_list[:]

        canvas.remove(b2)

        self.assertEquals(7, len(canvas.solver.constraints))

        cinfo = canvas.get_connection(l.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(l.handles()[-1])
        self.assertEquals(None, cinfo)

        undo()

        self.assertEquals(14, len(canvas.solver.constraints))

        cinfo = canvas.get_connection(l.handles()[0])
        self.assertEquals(b1, cinfo.connected)

        cinfo = canvas.get_connection(l.handles()[-1])
        self.assertEquals(b2, cinfo.connected)

        

# vim:sw=4:et:ai
