#!/usr/bin/env python

import pygtk
pygtk.require('2.0') 

import sys
import math
import gtk
from gaphas import Canvas, GtkView, View
from gaphas.examples import Box, Text, DefaultExampleTool
from gaphas.item import Line, NW, SE
from gaphas.tool import PlacementTool, HandleTool
from gaphas.painter import ItemPainter
from gaphas import state
from gaphas.util import text_extents

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


def create_window(canvas, title, zoom=1.0):
    view = GtkView()
    view.tool = DefaultExampleTool()

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

    b = gtk.Button('Move by (100, 50)')

    def on_clicked(button):
        global movable_item
        item = movable_item
        import time
        t1 = time.time()
        for i in range(20):
            item.matrix.translate(1, 1)
            item.request_update()
            canvas.update_matrix(item)
            # visualize each event:
            while gtk.events_pending():
                gtk.main_iteration()
        t2 = time.time()
        print 'move time: %0.2f' % (t2 - t1,)

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

def main():
    global movable_item
    if len(sys.argv) == 2:
        count = int(sys.argv[1])
    else:
        count = 1
    c=Canvas()

    create_window(c, 'View created before')

    # Add stuff to the canvas:

    movable_item=b=MyBox()
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

    # AJM: extra boxes:
    bb=Box()
    print 'box', bb
    bb.matrix.rotate(math.pi/4.)
    c.add(bb, parent=b)
    n = math.floor(count ** 0.5)
    for i in xrange(count):
        bb=Box()
        print 'box', bb
        x = int(i % n) * 20
        y = int(i / n) * 20
        bb.matrix.translate(x, y)
        bb.matrix.rotate(math.pi/4.0 * i / 10.0)
        c.add(bb, parent=b)

    for i in range(40):
        bb = MyBox()
        bb.width = bb.height = 15
        x = int(i % 4) * 20
        y = int(i / 4) * 20
        bb.matrix.translate(20 + x, 100 + y)
        c.add(bb)

    t=MyText('Single line')
    t.matrix.translate(70,70)
    c.add(t)

    l=MyLine()
    l.fyzzyness = 1
    l.handles()[1].pos = (30, 30)
    l.split_segment(0, 3)
    l.matrix.translate(30, 60)
    c.add(l)
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

    gtk.main()

if __name__ == '__main__':
    try:
        import cProfile
        import pstats
        cProfile.run('main()', 'demo-gaphas.prof')
        p = pstats.Stats('demo-gaphas.prof')
        p.strip_dirs().sort_stats('time').print_stats(20)
    except ImportError, ex:
        import hotshot, hotshot.stats
        import gc
        prof = hotshot.Profile('demo-gaphas.prof')
        prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load('demo-gaphas.prof')
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)

# vim: sw=4:et:
