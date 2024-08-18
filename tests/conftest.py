# ruff: noqa: F402, E402

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")


import pytest
import pytest_asyncio
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


@pytest_asyncio.fixture
async def view(canvas):
    view = GtkView(canvas)
    await view.update()
    return view


@pytest_asyncio.fixture
async def scrolled_window(view):
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_child(view)
    await view.update()
    return scrolled_window


@pytest.fixture
def window(view):
    window = Gtk.Window.new()
    window.set_child(view)
    yield window
    window.destroy()


@pytest_asyncio.fixture
async def box(canvas, connections, view):
    box = Box(connections)
    canvas.add(box)
    await view.update()
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
