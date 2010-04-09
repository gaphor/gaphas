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

__version__ = "$Revision$"
# $HeadURL$

try:
    import pygtk
except ImportError:
    pass
else:
    pygtk.require('2.0') 

import math
import gtk
import cairo
from gaphas import Canvas, GtkView, View
from gaphas.examples import Box, PortoBox, Text, FatLine, Circle
from gaphas.item import Line, NW, SE
from gaphas.tool import PlacementTool, HandleTool
from gaphas.segment import Segment
import gaphas.guide
from gaphas.painter import PainterChain, ItemPainter, HandlePainter, FocusedItemPainter, ToolPainter, BoundingBoxPainter
from gaphas import state
from gaphas.util import text_extents, text_underline
from gaphas.freehand import FreeHandPainter

from gaphas import painter
#painter.DEBUG_DRAW_BOUNDING_BOX = True

# Ensure data gets picked well:
import gaphas.picklers

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
        super(MyLine, self).__init__()
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
        cr.set_source_rgba(.3, .3, 1., .6)
        cr.stroke()


class UnderlineText(Text):

    def draw(self, context):
        cr = context.cairo
        text_underline(cr, 0, 0, "Some text(y)")
 

def create_window(canvas, title, zoom=1.0):
    view = GtkView()
    view.painter = PainterChain(). \
        append(FreeHandPainter(ItemPainter())). \
        append(HandlePainter()). \
        append(FocusedItemPainter()). \
        append(ToolPainter())
    view.bounding_box_painter = FreeHandPainter(BoundingBoxPainter())
    w = gtk.Window()
    w.set_title(title)
    h = gtk.HBox()
    w.add(h)

    # VBox contains buttons that can be used to manipulate the canvas:
    v = gtk.VBox()
    v.set_property('border-width', 3)
    v.set_property('spacing', 2)
    f = gtk.Frame()
    f.set_property('border-width', 1)
    f.add(v)
    h.pack_start(f, expand=False)

    v.add(gtk.Label('Item placement:'))
    
    b = gtk.Button('Add box')

    def on_clicked(button, view):
        #view.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))
        view.tool.grab(PlacementTool(view, factory(view, MyBox), HandleTool(), 2))

    b.connect('clicked', on_clicked, view)
    v.add(b)

    b = gtk.Button('Add line')

    def on_clicked(button):
        view.tool.grab(PlacementTool(view, factory(view, MyLine), HandleTool(), 1))

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('Zooming:'))
   
    b = gtk.Button('Zoom in')

    def on_clicked(button):
        view.zoom(1.2)

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Zoom out')

    def on_clicked(button):
        view.zoom(1/1.2)

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('Misc:'))

    b = gtk.Button('Split line')

    def on_clicked(button):
        if isinstance(view.focused_item, Line):
            segment = Segment(view.focused_item, view)
            segment.split_segment(0)
            view.queue_draw_item(view.focused_item)

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Delete focused')

    def on_clicked(button):
        if view.focused_item:
            canvas.remove(view.focused_item)
            #print 'items:', canvas.get_all_items()

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('State:'))
    b = gtk.ToggleButton('Record')

    def on_toggled(button):
        global undo_list
        if button.get_active():
            print 'start recording'
            del undo_list[:]
            state.subscribers.add(undo_handler)
        else:
            print 'stop recording'
            state.subscribers.remove(undo_handler)

    b.connect('toggled', on_toggled)
    v.add(b)

    b = gtk.Button('Play back')
    
    def on_clicked(self):
        global undo_list
        apply_me = list(undo_list)
        del undo_list[:]
        print 'Actions on the undo stack:', len(apply_me)
        apply_me.reverse()
        saveapply = state.saveapply
        for event in apply_me:
            print 'Undo: invoking', event
            saveapply(*event)
            print 'New undo stack size:', len(undo_list)
            # Visualize each event:
            #while gtk.events_pending():
            #    gtk.main_iteration()

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('Export:'))

    b = gtk.Button('Write demo.png')

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
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w), int(h))
        cr = cairo.Context(surface)
        svgview.matrix.translate(-svgview.bounding_box.x, -svgview.bounding_box.y)
        cr.save()
        svgview.paint(cr)

        cr.restore()
        cr.show_page()
        surface.write_to_png('demo.png')

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Write demo.svg')

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
        surface = cairo.SVGSurface('demo.svg', w, h)
        cr = cairo.Context(surface)
        svgview.matrix.translate(-svgview.bounding_box.x, -svgview.bounding_box.y)
        svgview.paint(cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    b.connect('clicked', on_clicked)
    v.add(b)

    
    b = gtk.Button('Dump QTree')

    def on_clicked(button, li):
        view._qtree.dump()

    b.connect('clicked', on_clicked, [0])
    v.add(b)


    b = gtk.Button('Pickle (save)')

    def on_clicked(button, li):
        f = open('demo.pickled', 'w')
        try:
            import cPickle as pickle
            pickle.dump(view.canvas, f)
        finally:
            f.close()

    b.connect('clicked', on_clicked, [0])
    v.add(b)


    b = gtk.Button('Unpickle (load)')

    def on_clicked(button, li):
        f = open('demo.pickled', 'r')
        try:
            import cPickle as pickle
            canvas = pickle.load(f)
            canvas.update_now()
        finally:
            f.close()
        create_window(canvas, 'Unpickled diagram')

    b.connect('clicked', on_clicked, [0])
    v.add(b)


    b = gtk.Button('Unpickle (in place)')

    def on_clicked(button, li):
        f = open('demo.pickled', 'r')
        try:
            import cPickle as pickle
            canvas = pickle.load(f)
        finally:
            f.close()
        #[i.request_update() for i in canvas.get_all_items()]
        canvas.update_now()
        view.canvas = canvas

    b.connect('clicked', on_clicked, [0])
    v.add(b)


    b = gtk.Button('Reattach (in place)')

    def on_clicked(button, li):
        view.canvas = None
        view.canvas = canvas

    b.connect('clicked', on_clicked, [0])
    v.add(b)


    # Add the actual View:

    t = gtk.Table(2,2)
    h.add(t)

    w.connect('destroy', gtk.main_quit)

    view.canvas = canvas
    view.zoom(zoom)
    view.set_size_request(150, 120)
    hs = gtk.HScrollbar(view.hadjustment)
    vs = gtk.VScrollbar(view.vadjustment)
    t.attach(view, 0, 1, 0, 1)
    t.attach(hs, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
    t.attach(vs, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)

    w.show_all()
    
    def handle_changed(view, item, what):
        print what, 'changed: ', item

    view.connect('focus-changed', handle_changed, 'focus')
    view.connect('hover-changed', handle_changed, 'hover')
    view.connect('selection-changed', handle_changed, 'selection')

    
def create_canvas(c=None):
    if not c:
        c = Canvas()
    b=MyBox()
    b.min_width = 20
    b.min_height = 30
    print 'box', b
    b.matrix=(1.0, 0.0, 0.0, 1, 20,20)
    b.width = b.height = 40
    c.add(b)

    bb=Box()
    print 'box', bb
    bb.matrix=(1.0, 0.0, 0.0, 1, 10,10)
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
    print 'box', bb
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)
#    for i in xrange(10):
#        bb=Box()
#        print 'box', bb
#        bb.matrix.rotate(math.pi/4.0 * i / 10.0)
#        c.add(bb, parent=b)

    b = PortoBox(60, 60)
    b.min_width = 40
    b.min_height = 50
    b.matrix.translate(55, 55)
    c.add(b)

    t = UnderlineText()
    t.matrix.translate(70,30)
    c.add(t)

    t = MyText('Single line')
    t.matrix.translate(70,70)
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
            t=MyText('Aligned text %d/%d' % (align_x, align_y),
                     align_x=align_x, align_y=align_y)
            t.matrix.translate(120, 200 + off_y)
            off_y += 30
            c.add(t)

    t=MyText('Multiple\nlines', multiline = True)
    t.matrix.translate(70,100)
    c.add(t)

    return c


def main():
    ##
    ## State handling (a.k.a. undo handlers)
    ##

    # First, activate the revert handler:
    state.observers.add(state.revert_handler)

    def print_handler(event):
        print 'event:', event

    c=Canvas()

    create_window(c, 'View created before')

    create_canvas(c)

    #state.subscribers.add(print_handler)

    ##
    ## Start the main application
    ##

    create_window(c, 'View created after')

    gtk.main()


if __name__ == '__main__':
    import sys
    if '-p' in sys.argv:
        print 'Profiling...'
        import hotshot, hotshot.stats
        prof = hotshot.Profile('demo-gaphas.prof')
        prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load('demo-gaphas.prof')
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)
    else:
        main()

# vim: sw=4:et:
