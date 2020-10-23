import gi
import pytest

from gaphas import state
from gaphas.canvas import Canvas
from gaphas.item import Element as Box
from gaphas.item import Line
from gaphas.tool import ConnectHandleTool
from gaphas.view import GtkView

# fmt: off
gi.require_version("Gtk", "3.0")  # noqa: isort:skip
from gi.repository import Gtk  # noqa: isort:skip
# fmt: on


class SimpleCanvas:
    """Creates a test canvas object.

    Adds a view, canvas, and handle connection tool to a test case. Two
    boxes and a line are added to the canvas as well.
    """

    def __init__(self):
        self.canvas = Canvas()

        self.box1 = Box()
        self.canvas.add(self.box1)
        self.box1.matrix.translate(100, 50)
        self.box1.width = 40
        self.box1.height = 40
        self.canvas.request_update(self.box1)

        self.box2 = Box()
        self.canvas.add(self.box2)
        self.box2.matrix.translate(100, 150)
        self.box2.width = 50
        self.box2.height = 50
        self.canvas.request_update(self.box2)

        self.line = Line()
        self.head = self.line.handles()[0]
        self.tail = self.line.handles()[-1]
        self.tail.pos = 100, 100
        self.canvas.add(self.line)

        self.canvas.update_now()
        self.view = GtkView()
        self.view.canvas = self.canvas

        self.win = Gtk.Window()
        self.win.add(self.view)
        self.view.show()
        self.view.update()
        self.win.show()

        self.tool = ConnectHandleTool(self.view)


@pytest.fixture()
def simple_canvas():
    """Creates a `SimpleCanvas`."""
    return SimpleCanvas()


@pytest.fixture(scope="module")
def undo_fixture():
    undo_list = []  # type: ignore[var-annotated]
    redo_list = []  # type: ignore[var-annotated]

    def undo():
        apply_me = list(undo_list)
        del undo_list[:]
        apply_me.reverse()
        for e in apply_me:
            state.saveapply(*e)
        redo_list[:] = undo_list[:]
        del undo_list[:]

    def undo_handler(event):
        undo_list.append(event)

    return undo, undo_handler, undo_list


@pytest.fixture()
def revert_undo(undo_fixture):
    state.observers.clear()
    state.subscribers.clear()
    state.observers.add(state.revert_handler)
    state.subscribers.add(undo_fixture[1])
    yield
    state.observers.remove(state.revert_handler)
    state.subscribers.remove(undo_fixture[1])
