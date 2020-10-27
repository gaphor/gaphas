#!/usr/bin/env python
"""A simple example containing two boxes and a line."""
import gi

from examples.exampleitems import Box
from gaphas import Canvas, GtkView
from gaphas.item import Line

# fmt: off
gi.require_version("Gtk", "3.0")  # noqa: isort:skip
from gi.repository import Gtk  # noqa: isort:skip
# fmt: on


def create_canvas(canvas, title):
    # Setup drawing window
    view = GtkView()
    view.canvas = canvas
    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(400, 400)
    win_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    window.add(win_box)
    win_box.pack_start(view, True, True, 0)

    # Draw first gaphas box
    b1 = Box(60, 60)
    b1.matrix.translate(10, 10)
    canvas.add(b1)

    # Draw second gaphas box
    b2 = Box(60, 60)
    b2.min_width = 40
    b2.min_height = 50
    b2.matrix.translate(170, 170)
    canvas.add(b2)

    # Draw gaphas line
    line = Line()
    line.matrix.translate(100, 60)
    canvas.add(line)
    line.handles()[1].pos = (30, 30)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)


if __name__ == "__main__":
    c = Canvas()
    create_canvas(c, "Simple Gaphas App")
    Gtk.main()
