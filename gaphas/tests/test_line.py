
import unittest
from gaphas.item import Line
from gaphas.canvas import Canvas
from gaphas import state


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

class LineTestCase(unittest.TestCase):

    def setUp(self):
        state.observers.add(state.revert_handler)
        state.subscribers.add(undo_handler)

    def tearDown(self):
        state.observers.remove(state.revert_handler)
        state.subscribers.remove(undo_handler)

    def test_orthogonal_horizontal_undo(self):
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        assert len(canvas.solver._constraints) == 2
        after_ortho = set(canvas.solver._constraints)

        del undo_list[:]
        line.horizontal = True

        assert len(canvas.solver._constraints) == 2

        undo()

        assert not line.horizontal
        assert len(canvas.solver._constraints) == 2, canvas.solver._constraints

        line.horizontal = True

        assert line.horizontal
        assert len(canvas.solver._constraints) == 2, canvas.solver._constraints

    def test_orthogonal_line_split_segment(self):
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        assert len(canvas.solver._constraints) == 2
        after_ortho = set(canvas.solver._constraints)
        assert len(line.handles()) == 3

        del undo_list[:]

        line.split_segment(0)

        assert len(canvas.solver._constraints) == 3
        assert len(line.handles()) == 4

        undo()

        assert len(canvas.solver._constraints) == 2
        assert len(line.handles()) == 3
        assert canvas.solver._constraints == after_ortho


# vim:sw=4:et
