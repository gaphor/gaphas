import gi
import pytest

from gaphas import state
from gaphas.canvas import Canvas
from gaphas.item import Element as Box
from gaphas.item import Line
from gaphas.view import GtkView

# fmt: off
gi.require_version("Gtk", "3.0")  # noqa: isort:skip
from gi.repository import Gtk  # noqa: isort:skip
# fmt: on


@pytest.fixture
def canvas():
    return Canvas()


@pytest.fixture
def connections(canvas):
    return canvas.connections


@pytest.fixture
def view(canvas):
    view = GtkView(canvas)
    # resize, like when a widget is configured
    view._qtree.resize((0, 0, 400, 400))
    view.update()
    return view


@pytest.fixture
def window(view):
    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.add(view)
    window.show_all()
    yield window
    window.destroy()


@pytest.fixture
def box(canvas, connections):
    box = Box(connections)
    canvas.add(box)
    return box


@pytest.fixture
def line(canvas, connections):
    line = Line(connections)
    line.tail.pos = 100, 100
    canvas.add(line)
    return line


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
