#!/usr/bin/env python
"""A simple example containing two boxes and a line.

"""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from gaphas import Canvas, GtkView
from gaphas.examples import Box
from gaphas.painter import DefaultPainter
from gaphas.item import Line
from gaphas.segment import Segment


def create_canvas(canvas, title):
    # Setup drawing window
    view = GtkView()
    view.painter = DefaultPainter()
    view.canvas = canvas
    window = Gtk.Window()
    window.set_title(title)
    window.set_default_size(400, 400)
    win_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    window.add(win_box)
    win_box.pack_start(view, True, True, 0)

    # Draw first gaphas box
    b1 = Box(60, 60)
    b1.matrix = (1.0, 0.0, 0.0, 1, 10, 10)
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


c = Canvas()
create_canvas(c, "Simple Gaphas App")
Gtk.main()
