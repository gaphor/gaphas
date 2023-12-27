#!/usr/bin/env python
# ruff: noqa: E402
"""A simple demo app.

It sports a small canvas and some trivial operations:

 - Add a line/box
 - Zoom in/out
 - Split a line segment
 - Delete focused item
 - Exports to SVG and PNG
"""
import math
import sys

import cairo
import gi

# fmt: off
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
# fmt: on

from examples.exampleitems import Box, Circle, Text
from gaphas import Canvas
from gaphas.geometry import Rectangle
from gaphas.guide import GuidePainter
from gaphas.item import Line
from gaphas.painter import (
    FreeHandPainter,
    HandlePainter,
    ItemPainter,
    PainterChain,
)
from gaphas.segment import LineSegmentPainter
from gaphas.tool import (
    hover_tool,
    item_tool,
    placement_tool,
    view_focus_tool,
    zoom_tools,
)
from gaphas.tool.itemtool import Segment
from gaphas.tool.rubberband import RubberbandPainter, RubberbandState, rubberband_tool
from gaphas.tool.scroll import pan_tool
from gaphas.view import GtkView

# Global undo list
undo_list = []


def undo_handler(event):
    global undo_list
    undo_list.append(event)


def factory(view, cls):
    """Simple canvas item factory."""

    def wrapper():
        item = cls(view.model.connections)
        view.model.add(item)
        return item

    return wrapper


class MyBox(Box):
    """Box with an example connection protocol."""


class MyLine(Line):
    """Line with experimental connection protocol."""

    def __init__(self, connections):
        super().__init__(connections)
        self.fuzziness = 2

    def draw_head(self, context):
        cr = context.cairo
        cr.move_to(0, 0)
        cr.line_to(10, 10)
        cr.stroke()
        # Start point for the line to the next handle
        cr.move_to(0, 0)

    def draw_tail(self, context):
        cr = context.cairo
        cr.line_to(0, 0)
        cr.line_to(10, 10)
        cr.stroke()


class MyText(Text):
    """Text with experimental connection protocol."""

    def draw(self, context):
        Text.draw(self, context)
        cr = context.cairo
        w, h = text_extents(cr, self.text, multiline=self.multiline)
        cr.rectangle(0, 0, w, h)
        cr.set_source_rgba(0.3, 0.3, 1.0, 0.6)
        cr.stroke()


class UnderlineText(Text):
    def draw(self, context):
        cr = context.cairo
        text_underline(cr, 0, 0, "Some text(y)")


def text_extents(cr, text, multiline=False):
    """Simple way to determine the size of a piece of text."""
    if not text:
        return 0, 0

    if multiline:
        width, height = 0, 0
        for line in text.split("\n"):
            _x_bear, _y_bear, w, h, _x_adv, _y_adv = cr.text_extents(line)
            width = max(width, w)
            height += h
    else:
        _x_bear, _y_bear, width, height, _x_adv, _y_adv = cr.text_extents(text)
        # width, height = width + x_bearing, height + y_bearing

    return width, height


def text_underline(cr, x, y, text, offset=1.5):
    """Draw text with underline."""
    x_bear, y_bear, w, h, x_adv, y_adv = cr.text_extents(text)
    cr.move_to(x, y - y_bear)
    cr.show_text(text)
    cr.move_to(x, y - y_bear + offset)
    cr.set_line_width(1.0)
    cr.rel_line_to(x_adv, 0)
    cr.stroke()


def rubberband_state(view):
    try:
        return view.rubberband_state
    except AttributeError:
        view.rubberband_state = RubberbandState()
        return view.rubberband_state


def apply_default_tool_set(view):
    view.remove_all_controllers()
    view.add_controller(item_tool())
    for tool in zoom_tools():
        view.add_controller(tool)
    view.add_controller(pan_tool())
    view.add_controller(view_focus_tool())

    view.add_controller(rubberband_tool(rubberband_state(view)))
    view.add_controller(hover_tool())
    return rubberband_state


def apply_placement_tool_set(view, item_type, handle_index):
    def unset_placement_tool(gesture, offset_x, offset_y):
        apply_default_tool_set(view)

    view.remove_all_controllers()
    tool = placement_tool(factory(view, item_type), handle_index)
    tool.connect("drag-end", unset_placement_tool)
    view.add_controller(tool)
    for tool in zoom_tools():
        view.add_controller(tool)
    view.add_controller(view_focus_tool())


def apply_painters(view):
    painter = FreeHandPainter(ItemPainter(view.selection))
    view.painter = (
        PainterChain()
        .append(painter)
        .append(HandlePainter(view))
        .append(LineSegmentPainter(view.selection))
        .append(GuidePainter(view))
        .append(RubberbandPainter(rubberband_state(view)))
    )
    view.bounding_box_painter = painter


def calculate_bounding_box(painter, items):
    surface = cairo.RecordingSurface(cairo.Content.COLOR_ALPHA, None)
    cr = cairo.Context(surface)
    painter.paint(items, cr)
    return Rectangle(*surface.ink_extents())


def create_window(canvas, title, zoom=1.0):  # noqa too complex
    view = GtkView()

    apply_default_tool_set(view)
    apply_painters(view)

    w = Gtk.Window()
    w.set_title(title)
    w.set_default_size(400, 120)
    h = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)

    def h_append(b):
        h.append(b)

    w.set_child(h)

    # VBox contains buttons that can be used to manipulate the canvas:
    v = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)

    def v_append(b):
        v.append(b)

    f = Gtk.Frame()
    f.set_child(v)
    h_append(f)

    v_append(Gtk.Label.new("Item placement:"))

    b = Gtk.Button.new_with_label("Add box")

    def on_add_box_clicked(_button):
        apply_placement_tool_set(view, MyBox, 2)

    b.connect("clicked", on_add_box_clicked)
    v_append(b)

    b = Gtk.Button.new_with_label("Add line")

    def on_add_line_clicked(_button):
        apply_placement_tool_set(view, MyLine, -1)

    b.connect("clicked", on_add_line_clicked)
    v_append(b)

    v_append(Gtk.Label.new("Zooming:"))

    b = Gtk.Button.new_with_label("Zoom in")

    def on_zoom_in_clicked(_button):
        view.zoom(1.2)

    b.connect("clicked", on_zoom_in_clicked)
    v_append(b)

    b = Gtk.Button.new_with_label("Zoom out")

    def on_zoom_out_clicked(_button):
        view.zoom(1 / 1.2)

    b.connect("clicked", on_zoom_out_clicked)
    v_append(b)

    v_append(Gtk.Label.new("Misc:"))

    b = Gtk.Button.new_with_label("Split line")

    def on_split_line_clicked(_button):
        selection = view.selection
        if isinstance(selection.focused_item, Line):
            segment = Segment(selection.focused_item, canvas)
            segment.split_segment(0)

    b.connect("clicked", on_split_line_clicked)
    v_append(b)

    b = Gtk.Button.new_with_label("Delete focused")

    def on_delete_focused_clicked(_button):
        if view.selection.focused_item:
            canvas.remove(view.selection.focused_item)

    b.connect("clicked", on_delete_focused_clicked)
    v_append(b)

    v_append(Gtk.Label.new("Export:"))

    b = Gtk.Button.new_with_label("Write demo.png")

    def on_write_demo_png_clicked(_button):
        assert view.model
        painter = ItemPainter()

        bounding_box = calculate_bounding_box(painter, canvas.get_all_items())

        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, int(bounding_box.width), int(bounding_box.height)
        )
        cr = cairo.Context(surface)
        cr.translate(-bounding_box.x, -bounding_box.y)
        painter.paint(items=list(view.model.get_all_items()), cairo=cr)
        cr.show_page()
        surface.write_to_png("demo.png")

    b.connect("clicked", on_write_demo_png_clicked)
    v_append(b)

    b = Gtk.Button.new_with_label("Write demo.svg")

    def on_write_demo_svg_clicked(button):
        assert view.model
        painter = ItemPainter()

        bounding_box = calculate_bounding_box(painter, canvas.get_all_items())

        surface = cairo.SVGSurface(
            "demo.svg", int(bounding_box.width), int(bounding_box.height)
        )
        cr = cairo.Context(surface)
        cr.translate(-bounding_box.x, -bounding_box.y)
        painter.paint(items=list(view.model.get_all_items()), cairo=cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    b.connect("clicked", on_write_demo_svg_clicked)
    v_append(b)

    b = Gtk.Button.new_with_label("Dump QTree")

    def on_dump_qtree_clicked(_button, li):
        view._qtree.dump()

    b.connect("clicked", on_dump_qtree_clicked, [0])
    v_append(b)

    b = Gtk.Button.new_with_label("Reattach (in place)")

    def on_reattach_clicked(_button, li):
        view.model = None
        view.model = canvas

    b.connect("clicked", on_reattach_clicked, [0])
    v_append(b)

    # Add the actual View:

    view.model = canvas
    view.zoom(zoom)
    view.set_size_request(150, 120)
    s = Gtk.ScrolledWindow.new()
    s.set_hexpand(True)
    s.set_child(view)
    h_append(s)

    w.present()

    w.connect("destroy", lambda w: app.quit())

    return w


def create_canvas(c=None):
    if not c:
        c = Canvas()
    b = MyBox(c.connections)
    b.min_width = 20
    b.min_height = 30
    b.matrix.translate(20, 20)
    b.width = b.height = 40
    c.add(b)

    bb = Box(c.connections)
    bb.matrix.translate(10, 10)
    c.add(bb, parent=b)

    bb = Box(c.connections)
    bb.matrix.rotate(math.pi / 1.567)
    c.add(bb, parent=b)

    circle = Circle()
    h1, h2 = circle.handles()
    circle.radius = 20
    circle.matrix.translate(50, 160)
    c.add(circle)

    pb = Box(c.connections, 60, 60)
    pb.min_width = 40
    pb.min_height = 50
    pb.matrix.translate(100, 20)
    c.add(pb)

    ut = UnderlineText()
    ut.matrix.translate(100, 130)
    c.add(ut)

    t = MyText("Single line")
    t.matrix.translate(100, 170)
    c.add(t)

    line = MyLine(c.connections)
    c.add(line)
    line.handles()[1].pos = (30, 30)
    segment = Segment(line, c)
    segment.split_segment(0, 3)
    line.matrix.translate(30, 80)
    line.orthogonal = True

    return c


app = Gtk.Application.new("org.gaphor.gaphas.Demo", 0)


def main():
    def activate(app):
        c = Canvas()

        win1 = create_window(c, "View created before")
        app.add_window(win1)
        create_canvas(c)
        win2 = create_window(c, "View created after")
        app.add_window(win2)

    app.connect("activate", activate)

    app.run()


if __name__ == "__main__":
    if "-p" in sys.argv:
        print("Profiling...")
        import hotshot
        import hotshot.stats

        prof = hotshot.Profile("demo-gaphas.prof")
        prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load("demo-gaphas.prof")
        stats.strip_dirs()
        stats.sort_stats("time", "calls")
        stats.print_stats(20)
    else:
        main()
