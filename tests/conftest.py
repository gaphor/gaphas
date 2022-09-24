import pytest
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.item import Element, Line
from gaphas.view import GtkView


class Box(Element):
    def draw(self, context):
        cr = context.cairo
        top_left = self.handles()[0].pos
        cr.rectangle(top_left.x, top_left.y, self.width, self.height)
        cr.stroke()


@pytest.fixture
def canvas():
    return Canvas()


@pytest.fixture
def connections(canvas):
    return canvas.connections


@pytest.fixture
def view(canvas):
    view = GtkView(canvas)
    # view.update()
    return view


@pytest.fixture
def scrolled_window(view):
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.add(
        view
    ) if Gtk.get_major_version() == 3 else scrolled_window.set_child(view)
    view.update()
    return scrolled_window


@pytest.fixture
def window(view):
    if Gtk.get_major_version() == 3:
        window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        window.add(view)
        window.show_all()
    else:
        window = Gtk.Window.new()
        window.set_child(view)
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
