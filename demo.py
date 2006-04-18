"""
A simple demo app.
"""

import pygtk
pygtk.require('2.0') 

import gtk
from view import View
from canvas import Canvas
from tool import DefaultToolChain
from examples import Box, Text

import math
w = gtk.Window()
t = gtk.Table(2,2)
w.add(t)
w.connect('destroy', gtk.main_quit)

v = View()
v.set_size_request(150, 150)
hs = gtk.HScrollbar(v.hadjustment)
vs = gtk.VScrollbar(v.vadjustment)
t.attach(v, 0, 1, 0, 1)
t.attach(hs, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
t.attach(vs, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)

c=Canvas()
v.canvas = c
v.tool = DefaultToolChain()

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

t=Text()
t.matrix.translate(70,70)
c.add(t)

w.show_all()

gtk.main()


# vim: sw=4:et:
