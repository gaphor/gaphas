#!/usr/bin/env python
"""A simple demo app.

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

from examples.exampleitems import Box, Circle, Text
from gaphas import Canvas, GtkView, state
from gaphas.canvas import Context
from gaphas.item import Line
from gaphas.painter import (
    BoundingBoxPainter,
    FocusedItemPainter,
    FreeHandPainter,
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
    """
    Set the event handler for the event.

    Args:
        event: (todo): write your description
    """
    global undo_list
    undo_list.append(event)


def factory(view, cls):
    """Simple canvas item factory."""

    def wrapper():
        """
        Creates the view that will be used for the view.

        Args:
        """
        item = cls(view.canvas.connections)
        view.canvas.add(item)
        return item

    return wrapper


def paint(view, cr):
    """
    Paint the view.

    Args:
        view: (todo): write your description
        cr: (todo): write your description
    """
    view.painter.paint(Context(cairo=cr, items=view.canvas.get_all_items(), area=None))


class MyBox(Box):
    """Box with an example connection protocol."""


class MyLine(Line):
    """Line with experimental connection protocol."""

    def __init__(self, connections):
        """
        Initialize the connection.

        Args:
            self: (todo): write your description
            connections: (todo): write your description
        """
        super().__init__(connections)
        self.fuzziness = 2

    def draw_head(self, context):
        """
        Draws a head.

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        cr = context.cairo
        cr.move_to(0, 0)
        cr.line_to(10, 10)
        cr.stroke()
        # Start point for the line to the next handle
        cr.move_to(0, 0)

    def draw_tail(self, context):
        """
        Draws a tail.

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        cr = context.cairo
        cr.line_to(0, 0)
        cr.line_to(10, 10)
        cr.stroke()


class MyText(Text):
    """Text with experimental connection protocol."""

    def draw(self, context):
        """
        Draws the context.

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        Text.draw(self, context)
        cr = context.cairo
        w, h = text_extents(cr, self.text, multiline=self.multiline)
        cr.rectangle(0, 0, w, h)
        cr.set_source_rgba(0.3, 0.3, 1.0, 0.6)
        cr.stroke()


class UnderlineText(Text):
    def draw(self, context):
        """
        Draws :: context

        Args:
            self: (todo): write your description
            context: (dict): write your description
        """
        cr = context.cairo
        text_underline(cr, 0, 0, "Some text(y)")


def create_window(canvas, title, zoom=1.0):  # noqa too complex
    """
    Function creates a new gtk.

    Args:
        canvas: (todo): write your description
        title: (str): write your description
        zoom: (str): write your description
    """
    view = GtkView()
    view.painter = (
        PainterChain()
        .append(FreeHandPainter(ItemPainter(view.selection)))
        .append(HandlePainter(view))
        .append(FocusedItemPainter(view))
        .append(ToolPainter(view))
    )
    view.bounding_box_painter = BoundingBoxPainter(
        FreeHandPainter(ItemPainter(view.selection))
    )
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

    def on_add_box_clicked(button, view):
        """
        Called when a button clicked.

        Args:
            button: (todo): write your description
            view: (todo): write your description
        """
        # view.window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.CROSSHAIR))
        view.tool.grab(PlacementTool(view, factory(view, MyBox), HandleTool(), 2))

    b.connect("clicked", on_add_box_clicked, view)
    v.add(b)

    b = Gtk.Button.new_with_label("Add line")

    def on_add_line_clicked(button):
        """
        Add a button clicked on button.

        Args:
            button: (todo): write your description
        """
        view.tool.grab(PlacementTool(view, factory(view, MyLine), HandleTool(), 1))

    b.connect("clicked", on_add_line_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Zooming:"))

    b = Gtk.Button.new_with_label("Zoom in")

    def on_zoom_in_clicked(button):
        """
        Zoom on_in_in_in_in_in_in_in_in_in_in_in_in_in_

        Args:
            button: (todo): write your description
        """
        view.zoom(1.2)

    b.connect("clicked", on_zoom_in_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Zoom out")

    def on_zoom_out_clicked(button):
        """
        Zoom out to zoom button.

        Args:
            button: (todo): write your description
        """
        view.zoom(1 / 1.2)

    b.connect("clicked", on_zoom_out_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Misc:"))

    b = Gtk.Button.new_with_label("Split line")

    def on_split_line_clicked(button):
        """
        Split selected button clicked on the selected

        Args:
            button: (str): write your description
        """
        selection = view.selection
        if isinstance(selection.focused_item, Line):
            segment = Segment(selection.focused_item, canvas)
            segment.split_segment(0)
            view.queue_redraw()

    b.connect("clicked", on_split_line_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Delete focused")

    def on_delete_focused_clicked(button):
        """
        Delete the selected item.

        Args:
            button: (todo): write your description
        """
        if view.selection.focused_item:
            canvas.remove(view.selection.focused_item)

    b.connect("clicked", on_delete_focused_clicked)
    v.add(b)

    v.add(Gtk.Label.new("State:"))
    b = Gtk.ToggleButton.new_with_label("Record")

    def on_toggled(button):
        """
        Handle the selected button.

        Args:
            button: (todo): write your description
        """
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

    def on_play_back_clicked(self):
        """
        Undo for back button clicked.

        Args:
            self: (todo): write your description
        """
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

    b.connect("clicked", on_play_back_clicked)
    v.add(b)

    v.add(Gtk.Label.new("Export:"))

    b = Gtk.Button.new_with_label("Write demo.png")

    def on_write_demo_png_clicked(button):
        """
        Write png to png.

        Args:
            button: (todo): write your description
        """
        painter = ItemPainter()

        # Update bounding boxes with a temporary CairoContext
        # (used for stuff like calculating font metrics)
        tmpsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        tmpcr = cairo.Context(tmpsurface)
        bounding_box = BoundingBoxPainter(painter).bounding_box(
            canvas.get_all_items(), tmpcr
        )
        tmpcr.show_page()
        tmpsurface.flush()

        surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, int(bounding_box.width), int(bounding_box.height)
        )
        cr = cairo.Context(surface)
        cr.translate(-bounding_box.x, -bounding_box.y)
        painter.paint(items=view.canvas.get_all_items(), cairo=cr)
        cr.show_page()
        surface.write_to_png("demo.png")

    b.connect("clicked", on_write_demo_png_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Write demo.svg")

    def on_write_demo_svg_clicked(button):
        """
        Callback for write button write_write button.

        Args:
            button: (todo): write your description
        """
        painter = ItemPainter()

        # Update bounding boxes with a temporaly CairoContext
        # (used for stuff like calculating font metrics)
        tmpsurface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        tmpcr = cairo.Context(tmpsurface)
        bounding_box = BoundingBoxPainter(painter).bounding_box(
            canvas.get_all_items(), tmpcr
        )
        tmpcr.show_page()
        tmpsurface.flush()

        surface = cairo.SVGSurface(
            "demo.svg", int(bounding_box.width), int(bounding_box.height)
        )
        cr = cairo.Context(surface)
        cr.translate(-bounding_box.x, -bounding_box.y)
        painter.paint(items=view.canvas.get_all_items(), cairo=cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    b.connect("clicked", on_write_demo_svg_clicked)
    v.add(b)

    b = Gtk.Button.new_with_label("Dump QTree")

    def on_dump_qtree_clicked(button, li):
        """
        Trigdump on button is_clicked.

        Args:
            button: (todo): write your description
            li: (todo): write your description
        """
        view._qtree.dump()

    b.connect("clicked", on_dump_qtree_clicked, [0])
    v.add(b)

    b = Gtk.Button.new_with_label("Reattach (in place)")

    def on_reattach_clicked(button, li):
        """
        Called when a button is clicked.

        Args:
            button: (todo): write your description
            li: (todo): write your description
        """
        view.canvas = None
        view.canvas = canvas

    b.connect("clicked", on_reattach_clicked, [0])
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
        """
        Called when an item is changed.

        Args:
            view: (todo): write your description
            item: (todo): write your description
            what: (todo): write your description
        """
        print(what, "changed: ", item)

    view.selection.connect("focus-changed", handle_changed, "focus")
    view.selection.connect("hover-changed", handle_changed, "hover")
    view.selection.connect("selection-changed", handle_changed, "selection")


def create_canvas(c=None):
    """
    Creates a canvas

    Args:
        c: (todo): write your description
    """
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


def main():
    """
    Main function.

    Args:
    """
    # State handling (a.k.a. undo handlers)

    # First, activate the revert handler:
    state.observers.add(state.revert_handler)

    def print_handler(event):
        """
        Prints a handler

        Args:
            event: (todo): write your description
        """
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
