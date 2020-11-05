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
    """
    Returns a list of the given canvas.

    Args:
    """
    return Canvas()


@pytest.fixture
def connections(canvas):
    """
    Return the list of connections to a given canvas.

    Args:
        canvas: (str): write your description
    """
    return canvas.connections


@pytest.fixture
def view(canvas):
    """
    Creates the view tovas

    Args:
        canvas: (todo): write your description
    """
    view = GtkView(canvas)
    # resize, like when a widget is configured
    view._qtree.resize((0, 0, 400, 400))
    view.update()
    return view


@pytest.fixture
def window(view):
    """
    Destroy a window.

    Args:
        view: (str): write your description
    """
    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.add(view)
    window.show_all()
    yield window
    window.destroy()


@pytest.fixture
def box(canvas, connections):
    """
    Adds a box to the canvas.

    Args:
        canvas: (todo): write your description
        connections: (todo): write your description
    """
    box = Box(connections)
    canvas.add(box)
    return box


@pytest.fixture
def line(canvas, connections):
    """
    Adds a line

    Args:
        canvas: (array): write your description
        connections: (todo): write your description
    """
    line = Line(connections)
    line.tail.pos = 100, 100
    canvas.add(line)
    return line


@pytest.fixture(scope="module")
def undo_fixture():
    """
    Undo changes to the last state.

    Args:
    """
    undo_list = []  # type: ignore[var-annotated]
    redo_list = []  # type: ignore[var-annotated]

    def undo():
        """
        Undo the last changes

        Args:
        """
        apply_me = list(undo_list)
        del undo_list[:]
        apply_me.reverse()
        for e in apply_me:
            state.saveapply(*e)
        redo_list[:] = undo_list[:]
        del undo_list[:]

    def undo_handler(event):
        """
        Add the event handler.

        Args:
            event: (todo): write your description
        """
        undo_list.append(event)

    return undo, undo_handler, undo_list


@pytest.fixture()
def revert_undo(undo_fixture):
    """
    Rebuilds the last state.

    Args:
        undo_fixture: (str): write your description
    """
    state.observers.clear()
    state.subscribers.clear()
    state.observers.add(state.revert_handler)
    state.subscribers.add(undo_fixture[1])
    yield
    state.observers.remove(state.revert_handler)
    state.subscribers.remove(undo_fixture[1])
