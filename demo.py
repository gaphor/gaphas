"""
A simple demo app.
"""

__version__ = "$Revision$"
# $HeadURL$

import pygtk
pygtk.require('2.0') 

import math
import gtk
from view import View
from canvas import Canvas
from examples import Box, Text
from item import Line
from tool import PlacementTool, HandleTool


def create_window(canvas, zoom=1.0):
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

    def on_clicked(button):
        v.tool.grab(PlacementTool(Box, HandleTool(), 2))

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Add line')

    def on_clicked(button):
        v.tool.grab(PlacementTool(Line, HandleTool(), 1))

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('Zooming:'))
   
    b = gtk.Button('Zoom in')

    def on_clicked(button):
        v.zoom(1.2)

    b.connect('clicked', on_clicked)
    v.add(b)

    b = gtk.Button('Zoom out')

    def on_clicked(button):
        v.zoom(1/1.2)

    b.connect('clicked', on_clicked)
    v.add(b)

    v.add(gtk.Label('Misc:'))

    b = gtk.Button('Split line')

    def on_clicked(button):
        if isinstance(v.focused_item, Line):
            v.focused_item.split_segment(0)
            v.queue_draw_item(v.focused_item, handles=True)

    b.connect('clicked', on_clicked)
    v.add(b)

    # Add the actual View:

    t = gtk.Table(2,2)
    h.add(t)

    w.connect('destroy', gtk.main_quit)

    v = View()
    v.canvas = canvas
    v.zoom(zoom)
    v.set_size_request(150, 120)
    hs = gtk.HScrollbar(v.hadjustment)
    vs = gtk.VScrollbar(v.vadjustment)
    t.attach(v, 0, 1, 0, 1)
    t.attach(hs, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
    t.attach(vs, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)

    # Set the placement tool as tool for the first button press.
    #v.tool.grab(PlacementTool(Box, HandleTool(), 2))

    w.show_all()

c=Canvas()

create_window(c)
#create_window(c, zoom=1.3)

# Add stuff to the canvas:

b=Box()
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

l=Line()
l.fyzzyness = 1
l.handles()[1].pos = (30, 30)
l.split_segment(0, 3)
l.matrix.translate(30, 60)
c.add(l)
l.orthogonal = True

t=Text()
t.matrix.translate(70,70)
c.add(t)


gtk.main()


# vim: sw=4:et:
