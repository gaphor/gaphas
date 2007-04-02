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

import pygtk
pygtk.require('2.0') 

import math
import gtk
import cairo
from gaphas import Canvas, GtkView, View
from gaphas.examples import Box, Text, DefaultExampleTool
from gaphas.item import Line, NW, SE
from gaphas.tool import PlacementTool, HandleTool
from gaphas.painter import ItemPainter
from gaphas import state

# Global undo list
undo_list = []

def undo_handler(event):
    global undo_list
    undo_list.append(event)


class MyBox(Box):
    """Box with an example connection protocol.
    """

class MyLine(Line):
    """Line with experimental connection protocol.
    """
    
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
    """Text with experimental connection protocol.
    """
    pass


def create_window(canvas, zoom=1.0):
    view = GtkView()
    view.tool = DefaultExampleTool()

    w = gtk.Window()
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
        view.tool.grab(PlacementTool(MyBox, HandleTool(), 2))

    b.connect('clicked', on_clicked, view)
    v.add(b)

    b = gtk.Button('Add line')

    def on_clicked(button):
        view.tool.grab(PlacementTool(MyLine, HandleTool(), 1))

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
            view.focused_item.split_segment(0)
            view.queue_draw_item(view.focused_item, handles=True)

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Delete focused')

    def on_clicked(button):
        if view.focused_item:
            canvas.remove(view.focused_item)
            print 'items:', canvas.get_all_items()

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
        apply_me.reverse()
        saveapply = state.saveapply
        for event in apply_me:
            saveapply(*event)
            # Visualize each event:
            while gtk.events_pending():
                gtk.main_iteration()

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
        svgview.matrix.translate(-svgview.bounding_box.x0, -svgview.bounding_box.y0)
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
        svgview.matrix.translate(-svgview.bounding_box.x0, -svgview.bounding_box.y0)
        svgview.paint(cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    b.connect('clicked', on_clicked)
    v.add(b)

    
#    b = gtk.Button('Cursor')
#
#    def on_clicked(button, li):
#        c = li[0]
#        li[0] = (c+2) % 154
#        button.set_label('Cursor %d' % c)
#        button.window.set_cursor(gtk.gdk.Cursor(c))
#
#    b.connect('clicked', on_clicked, [0])
#    v.add(b)

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

if __name__ == '__main__':
    c=Canvas()

    create_window(c)

    # Add stuff to the canvas:

    b=MyBox()
    b.min_width = 20
    b.min_height = 30
    print 'box', b
    b.matrix=(1.0, 0.0, 0.0, 1, 20,20)
    b.width=b.height = 40
    c.add(b)

    bb=Box()
    print 'box', bb
    bb.matrix=(1.0, 0.0, 0.0, 1, 10,10)
    c.add(bb, parent=b)
    #v.selected_items = bb

    bb=Box()
    print 'box', bb
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)

    l=MyLine()
    l.fyzzyness = 1
    l.handles()[1].pos = (30, 30)
    l.split_segment(0, 3)
    l.matrix.translate(30, 60)
    c.add(l)
    l.orthogonal = True

    t=MyText()
    t.matrix.translate(70,70)
    c.add(t)

    ##
    ## State handling (a.k.a. undo handlers)
    ##

    # First, activate the revert handler:
    state.observers.add(state.revert_handler)

    def print_handler(event):
        print 'event:', event

    #state.subscribers.add(print_handler)


    ##
    ## Start the main application
    ##

    gtk.main()


# vim: sw=4:et:
