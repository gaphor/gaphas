#!/usr/bin/env python
"""
A simple demo app.

It sports a small canvas and some trivial operations:

 - Add a line/box
 - Zoom in/out
 - Split a line segment
 - Delete focused item
 - Record state changes
 - Play back state changes (= undo !) With visual updates
 - Exports to SVG and PNG

"""
import math

import cairo
import gi

import gaphas.picklers
from gaphas import Canvas, GtkView, View, state
from gaphas.examples import Box, Circle, FatLine, PortoBox, Text
from gaphas.freehand import FreeHandPainter
from gaphas.item import Line
from gaphas.painter import (
    BoundingBoxPainter,
    FocusedItemPainter,
    HandlePainter,
    ItemPainter,
    PainterChain,
    ToolPainter,
)
from gaphas.segment import Segment
from gaphas.tool import HandleTool, PlacementTool
from gaphas.util import text_extents, text_underline

# fmt: off
gi.require_version("Gtk", "3.0")  # noqa: isort:skip
from gi.repository import Gtk  # noqa: isort:skip
# fmt: on

# painter.DEBUG_DRAW_BOUNDING_BOX = True

# Global undo list
undo_list = []


def undo_handler(event):
    global undo_list
    undo_list.append(event)


def factory(view, cls):
    """
    Simple canvas item factory.
    """

    def wrapper():
        item = cls()
        view.canvas.add(item)
        return item

    return wrapper


class MyBox(Box):
    """Box with an example connection protocol.
    """


class MyLine(Line):
    """Line with experimental connection protocol.
    """

    def __init__(self):
        super().__init__()
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
    """
    Text with experimental connection protocol.
    """

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


def create_window(canvas, title, zoom=1.0):
    view = GtkView()
    view.painter = (
        PainterChain()
        .append(FreeHandPainter(ItemPainter()))
        .append(HandlePainter())
        .append(FocusedItemPainter())
        .append(ToolPainter())
    )
    view.bounding_box_painter = BoundingBoxPainter(FreeHandPainter(ItemPainter()))
    w = Gtk.Window()
    w.set_title(title)
    w.set_default_size(400, 120)
    h = Gtk.HBox()
    w.add(h)

    # VBox contains buttons that can be used to manipulate the canvas:
    v = Gtk.VBox()
    v.set_property("border-width", 3)
    v.set_property("spacing", 2)
    f = Gtk.Frame()
    f.set_property("border-width", 1)
    f.add(v)
    h.pack_start(f, False, True, 0)

    v.add(Gtk.Label.new("Item placement:"))

    b = Gtk.Button.new_with_label("Add box")

    def on_clicked(button, view):
        # view.window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.CROSSHAIR))
        view.tool.grab(PlacementTool(view, factory(view, MyBox), HandleTool(), 2))

    b.connect("clicked", on_clicked, view)
    v.add(b)

    b = Gtk.Button.new_with_label("Add line")

    def on_clicked(button):
        view.tool.grab(PlacementTool(view, factory(view, MyLine), HandleTool(), 1))

    b.connect("clicked", on_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Zooming:"))

    b = Gtk.Button.new_with_label("Zoom in")

    def on_clicked(button):
        view.zoom(1.2)

    b.connect("clicked", on_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Zoom out")

    def on_clicked(button):
        view.zoom(1 / 1.2)

    b.connect("clicked", on_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Misc:"))

    b = Gtk.Button.new_with_label("Split line")

    def on_clicked(button):
        if isinstance(view.focused_item, Line):
            segment = Segment(view.focused_item, view)
            segment.split_segment(0)
            view.queue_draw_item(view.focused_item)

    b.connect("clicked", on_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Delete focused")

    def on_clicked(button):
        if view.focused_item:
            canvas.remove(view.focused_item)

    b.connect("clicked", on_clicked)
    v.add(b)

    v.add(Gtk.Label.new("State:"))
    b = Gtk.ToggleButton.new_with_label("Record")

    def on_toggled(button):
        global undo_list
        if button.get_active():
            print("start recording")
            del undo_list[:]
            state.subscribers.add(undo_handler)
        else:
            print("stop recording")
            state.subscribers.remove(undo_handler)

    b.connect("toggled", on_toggled)
    v.add(b)

    b = Gtk.Button.new_with_label("Play back")

    def on_clicked(self):
        global undo_list
        apply_me = list(undo_list)
        del undo_list[:]
        print("Actions on the undo stack:", len(apply_me))
        apply_me.reverse()
        saveapply = state.saveapply
        for event in apply_me:
            print("Undo: invoking", event)
            saveapply(*event)
            print("New undo stack size:", len(undo_list))
            # Visualize each event:
            # while Gtk.events_pending():
            #    Gtk.main_iteration()

    b.connect("clicked", on_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Export:"))

    b = Gtk.Button.new_with_label("Write demo.png")

    def on_clicked(button):
        svgview = View(view.canvas)
        svgview.painter = ItemPainter()

        # Update bounding boxes with a temporary CairoContext
        # (used for stuff like calculating font metrics)
        tmpsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        tmpcr = cairo.Context(tmpsurface)
        svgview.update_bounding_box(tmpcr)
        tmpcr.show_page()
        tmpsurface.flush()

        w, h = svgview.bounding_box.width, svgview.bounding_box.height
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))
        cr = cairo.Context(surface)
        svgview.matrix.translate(-svgview.bounding_box.x, -svgview.bounding_box.y)
        cr.save()
        svgview.paint(cr)

        cr.restore()
        cr.show_page()
        surface.write_to_png("demo.png")

    b.connect("clicked", on_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Write demo.svg")

    def on_clicked(button):
        svgview = View(view.canvas)
        svgview.painter = ItemPainter()

        # Update bounding boxes with a temporaly CairoContext
        # (used for stuff like calculating font metrics)
        tmpsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        tmpcr = cairo.Context(tmpsurface)
        svgview.update_bounding_box(tmpcr)
        tmpcr.show_page()
        tmpsurface.flush()

        w, h = svgview.bounding_box.width, svgview.bounding_box.height
        surface = cairo.SVGSurface("demo.svg", w, h)
        cr = cairo.Context(surface)
        svgview.matrix.translate(-svgview.bounding_box.x, -svgview.bounding_box.y)
        svgview.paint(cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    b.connect("clicked", on_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Dump QTree")

    def on_clicked(button, li):
        view._qtree.dump()

    b.connect("clicked", on_clicked, [0])
    v.add(b)

    b = Gtk.Button.new_with_label("Pickle (save)")

    def on_clicked(button, li):
        f = open("demo.pickled", "wb")
        try:
            import pickle

            pickle.dump(view.canvas, f)
        finally:
            f.close()

    b.connect("clicked", on_clicked, [0])
    v.add(b)

    b = Gtk.Button.new_with_label("Unpickle (load)")

    def on_clicked(button, li):
        f = open("demo.pickled", "rb")
        try:
            import pickle

            canvas = pickle.load(f)
            canvas.update_now()
        finally:
            f.close()
        create_window(canvas, "Unpickled diagram")

    b.connect("clicked", on_clicked, [0])
    v.add(b)

    b = Gtk.Button.new_with_label("Unpickle (in place)")

    def on_clicked(button, li):
        f = open("demo.pickled", "rb")
        try:
            import pickle

            canvas = pickle.load(f)
        finally:
            f.close()
        # [i.request_update() for i in canvas.get_all_items()]
        canvas.update_now()
        view.canvas = canvas

    b.connect("clicked", on_clicked, [0])
    v.add(b)

    b = Gtk.Button.new_with_label("Reattach (in place)")

    def on_clicked(button, li):
        view.canvas = None
        view.canvas = canvas

    b.connect("clicked", on_clicked, [0])
    v.add(b)

    # Add the actual View:

    view.canvas = canvas
    view.zoom(zoom)
    view.set_size_request(150, 120)
    s = Gtk.ScrolledWindow.new()
    s.set_hexpand(True)
    s.add(view)
    h.add(s)

    w.show_all()

    w.connect("destroy", Gtk.main_quit)

    def handle_changed(view, item, what):
        print(what, "changed: ", item)

    view.connect("focus-changed", handle_changed, "focus")
    view.connect("hover-changed", handle_changed, "hover")
    view.connect("selection-changed", handle_changed, "selection")


def create_canvas(c=None):
    if not c:
        c = Canvas()
    b = MyBox()
    b.min_width = 20
    b.min_height = 30
    b.matrix = (1.0, 0.0, 0.0, 1, 20, 20)
    b.width = b.height = 40
    c.add(b)

    bb = Box()
    bb.matrix = (1.0, 0.0, 0.0, 1, 10, 10)
    c.add(bb, parent=b)

    fl = FatLine()
    fl.height = 50
    fl.matrix.translate(100, 100)
    c.add(fl)

    circle = Circle()
    h1, h2 = circle.handles()
    circle.radius = 20
    circle.matrix.translate(50, 100)
    c.add(circle)

    # AJM: extra boxes:
    bb = Box()
    bb.matrix.rotate(math.pi / 1.567)
    c.add(bb, parent=b)
    # for i in xrange(10):
    #     bb = Box()
    #     print('box', bb)
    #     bb.matrix.rotate(math.pi/4.0 * i / 10.0)
    #     c.add(bb, parent=b)

    b = PortoBox(60, 60)
    b.min_width = 40
    b.min_height = 50
    b.matrix.translate(55, 55)
    c.add(b)

    t = UnderlineText()
    t.matrix.translate(70, 30)
    c.add(t)

    t = MyText("Single line")
    t.matrix.translate(70, 70)
    c.add(t)

    l = MyLine()
    c.add(l)
    l.handles()[1].pos = (30, 30)
    segment = Segment(l, view=None)
    segment.split_segment(0, 3)
    l.matrix.translate(30, 60)
    l.orthogonal = True

    off_y = 0
    for align_x in (-1, 0, 1):
        for align_y in (-1, 0, 1):
            t = MyText(
                f"Aligned text {align_x:d}/{align_y:d}",
                align_x=align_x,
                align_y=align_y,
            )
            t.matrix.translate(120, 200 + off_y)
            off_y += 30
            c.add(t)

    t = MyText("Multiple\nlines", multiline=True)
    t.matrix.translate(70, 100)
    c.add(t)

    return c


def main():
    # State handling (a.k.a. undo handlers)

    # First, activate the revert handler:
    state.observers.add(state.revert_handler)

    def print_handler(event):
        print("event:", event)

    c = Canvas()

    create_window(c, "View created before")

    create_canvas(c)

    # state.subscribers.add(print_handler)

    # Start the main application

    create_window(c, "View created after")

    Gtk.main()


if __name__ == "__main__":
    import sys

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
