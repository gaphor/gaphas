#!/usr/bin/env python
# ruff: noqa: E402
"""A simple example containing two boxes and a line."""

import gi

# fmt: off
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from gaphas import Canvas, Line
from gaphas.tool import hover_tool, item_tool, view_focus_tool, zoom_tool
from gaphas.view import GtkView
from examples.exampleitems import Box
# fmt: on


def apply_default_tool_set(view):
    view.remove_all_controllers()
    view.add_controller(item_tool())
    view.add_controller(zoom_tool())
    view.add_controller(view_focus_tool())
    view.add_controller(hover_tool())


def create_canvas(canvas, title):
    # Setup drawing window
    view = GtkView()
    view.model = canvas
    apply_default_tool_set(view)

    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(400, 400)
    win_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    window.add(win_box)
    win_box.pack_start(view, True, True, 0)

    # Draw first gaphas box
    b1 = Box(canvas.connections, 60, 60)
    b1.matrix.translate(10, 10)
    canvas.add(b1)

    # Draw second gaphas box
    b2 = Box(canvas.connections, 60, 60)
    b2.min_width = 40
    b2.min_height = 50
    b2.matrix.translate(170, 170)
    canvas.add(b2)

    # Draw gaphas line
    line = Line(canvas.connections)
    line.matrix.translate(100, 60)
    canvas.add(line)
    line.handles()[1].pos = (30, 30)

    window.show_all()
    window.connect("destroy", Gtk.main_quit)


if __name__ == "__main__":
    c = Canvas()
    create_canvas(c, "Simple Gaphas App")
    Gtk.main()
