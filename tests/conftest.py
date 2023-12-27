# ruff: noqa: F402, E402
import os

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")


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
    # view.update()
    return GtkView(canvas)


@pytest.fixture
def scrolled_window(view):
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_child(view)
    view.update()
    return scrolled_window


@pytest.fixture
def window(view):
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
