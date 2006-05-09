#!/usr/bin/env python
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
from item import Line, NW, SE
from tool import PlacementTool, HandleTool
from constraint import LineConstraint
from geometry import point_on_rectangle, distance_rectangle_point

DEFAULT_POINTER = gtk.gdk.LEFT_PTR

def handle_tool_glue(self, view, item, handle, wx, wy):
    """MixIn method for HandleTool. It allows the tool to glue
    to a Box or (other) Line item.
    The distance from the item to the handle is determined in canvas
    coordinates, using a 10 pixel glue distance.
    """
    if not handle.connectable:
        return
    matrix_w2i = view.canvas.get_matrix_w2i
    matrix_i2w = view.canvas.get_matrix_i2w

    # Make glue distance depend on the zoom ratio (should be about 10 pixels)
    glue_distance, dummy = view.transform_distance_c2w(10, 0)
    glue_point = None
    glue_item = None
    for i in view.canvas.get_all_items():
        if not i is item:
            ix, iy = matrix_w2i(i).transform_point(wx, wy)
            try:
                distance, point = i.glue(item, handle, ix, iy)
                #print distance, point
                # Transform distance to world coordinates
                distance, dumy = matrix_i2w(i).transform_distance(distance, 0)
                if distance < glue_distance:
                    glue_distance = distance
                    glue_point = matrix_i2w(i).transform_point(*point)
                    glue_item = i
            except AttributeError:
                pass
    if glue_point:
        handle.x, handle.y = matrix_w2i(item).transform_point(*glue_point)
    return glue_item

HandleTool.glue = handle_tool_glue

def handle_tool_connect(self, view, item, handle, wx, wy):
    """Connect a handle to another item.

    In this "method" the following assumptios are made:
     1. The only item that accepts handle connections are the MyBox instances
     2. The only items with connectable handles are Line's
     
    """
    def side(handle, glued):
        if handle.x == glued.handles()[0].x:
            side = 0
        elif handle.y == glued.handles()[1].y:
            side = 1
        elif handle.x == glued.handles()[2].x:
            side = 2
        else:
            side = 3
        return side

    glue_item = self.glue(view, item, handle, wx, wy)
    if glue_item and glue_item is handle.connected_to:
        s = side(handle, glue_item)
        view.canvas.solver.remove_constraint(handle._connect_constraint)
        handle._connect_constraint = LineConstraint(view.canvas, glue_item, glue_item.handles()[s], glue_item.handles()[(s+1)%4], item, handle)
        view.canvas.solver.add_constraint(handle._connect_constraint)
        return

    # drop old connetion
    if handle.connected_to:
        # remove constraints
        try:
            view.canvas.solver.remove_constraint(handle._connect_constraint)
        except AttributeError:
            pass # no _connect_constraints attribute
        handle._connect_constraint = None
        handle.connected_to = None

    if glue_item:
        if isinstance(glue_item, MyBox):
            s = side(handle, glue_item)
            # Make a constraint that keeps into account item coordinates.
            handle._connect_constraint = LineConstraint(view.canvas, glue_item, glue_item.handles()[s], glue_item.handles()[(s+1)%4], item, handle)
            view.canvas.solver.add_constraint(handle._connect_constraint)
            handle.connected_to = glue_item

        pass # conenct to glue_item

HandleTool.connect = handle_tool_connect

def handle_tool_disconnect(self, view, item, handle):
    if handle.connected_to:
        handle._connect_constraint.disabled = True

HandleTool.disconnect = handle_tool_disconnect


class MyBox(Box):
    """Box with an example connection protocol.
    """

    def glue(self, item, handle, x, y):
        h = self._handles
        hnw = h[NW]
        hse = h[SE]
        r = (float(hnw.x), float(hnw.y), float(hse.x), float(hse.y))
        por = point_on_rectangle(r, (x, y), border=True)
        #print 'Point', r, (x, y), por
        return distance_rectangle_point(r, (x, y)), por

    def constrain(self, handle, x, y):
        pass

class MyLine(Line):
    """Line with experimental connection protocol.
    """
    pass


class MyText(Text):
    """Text with experimental connection protocol.
    """
    pass


def create_window(canvas, zoom=1.0):
    view = View()
    
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

c=Canvas()

create_window(c)
#create_window(c, zoom=1.3)

# Add stuff to the canvas:

b=MyBox()
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


gtk.main()


# vim: sw=4:et:
