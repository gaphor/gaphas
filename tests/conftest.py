import gi
import pytest

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
    line.tail.pos = (100, 100)
    canvas.add(line)
    return line


@pytest.fixture
def handler():
    events = []

    def handler(*args):
        events.append(args)

    handler.events = events  # type: ignore[attr-defined]
    return handler
