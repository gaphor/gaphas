import unittest
from gaphas.item import Line
from gaphas.canvas import Canvas
from gaphas import state
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
        self.assertEqual(1, len(line.ports()))

    def test_orthogonal_horizontal_undo(self):
        """Test orthogonal line constraints bug (#107)
        """
        canvas = Canvas()
        line = Line()
        canvas.add(line)
        assert not line.horizontal
        assert len(canvas.solver._constraints) == 0

        segment = Segment(line, None)
        segment.split_segment(0)

        line.orthogonal = True

        self.assertEqual(2, len(canvas.solver._constraints))
        after_ortho = set(canvas.solver._constraints)

        del undo_list[:]
        line.horizontal = True

        self.assertEqual(2, len(canvas.solver._constraints))

        undo()

        self.assertFalse(line.horizontal)
        self.assertEqual(2, len(canvas.solver._constraints))

        line.horizontal = True

        self.assertTrue(line.horizontal)
        self.assertEqual(2, len(canvas.solver._constraints))

    def test_orthogonal_line_undo(self):
        """Test orthogonal line undo
        """
        canvas = Canvas()
        line = Line()
        canvas.add(line)

        segment = Segment(line, None)
        segment.split_segment(0)

        # start with no orthogonal constraints
        assert len(canvas.solver._constraints) == 0

        line.orthogonal = True

        # check orthogonal constraints
        self.assertEqual(2, len(canvas.solver._constraints))
        self.assertEqual(3, len(line.handles()))

        undo()

        self.assertFalse(line.orthogonal)
        self.assertEqual(0, len(canvas.solver._constraints))
        self.assertEqual(2, len(line.handles()))


# vim:sw=4:et
