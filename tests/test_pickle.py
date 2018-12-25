from __future__ import print_function

import io
import pickle
from builtins import object

import cairo
import pytest
from future import standard_library
from gi.repository import Gtk

from examples import demo
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Element, Line
from gaphas.view import View, GtkView

# Ensure extra pickle reducers/reconstructors are loaded:
import gaphas.picklers

standard_library.install_aliases()


class MyPickler(pickle.Pickler):
    def save(self, obj, save_persistent_id=True):
        try:
            return pickle.Pickler.save(self, obj)
        except pickle.PicklingError as e:
            print("Error while pickling", obj, self.dispatch.get(type(obj)))
            raise e


class MyDisconnect(object):
    """Create a disconnect object.

    The disconnect object should be located at top-level, so the pickle code
    can find it.

    """

    def __call__(self):
        pass


class CanvasFixture(object):
    def __init__(self):
        self.canvas = Canvas()
        self.box = Box()
        self.box2 = Box()
        self.line = Line()


@pytest.fixture()
def canvas_fixture():
    cf = CanvasFixture()
    cf.canvas.add(cf.box)
    cf.box.matrix.translate(100, 50)
    cf.box.matrix.rotate(50)
    cf.canvas.add(cf.box2, parent=cf.box)

    cf.line.handles()[0].visible = False
    cf.line.handles()[0].connected_to = cf.box
    cf.line.handles()[0].disconnect = MyDisconnect()
    cf.line.handles()[0].connection_data = 1

    cf.canvas.add(cf.line)

    cf.canvas.update()

    return cf


def test_pickle_element():
    item = Element()

    pickled = pickle.dumps(item)
    i2 = pickle.loads(pickled)

    assert i2
    assert len(i2.handles()) == 4


def test_pickle_line():
    item = Line()

    pickled = pickle.dumps(item)
    i2 = pickle.loads(pickled)

    assert i2
    assert len(i2.handles()) == 2


def test_pickle(canvas_fixture):
    pickled = pickle.dumps(canvas_fixture.canvas)
    pickle.loads(pickled)

    assert type(canvas_fixture.canvas._tree.nodes[0]) is Box
    assert type(canvas_fixture.canvas._tree.nodes[1]) is Box
    assert type(canvas_fixture.canvas._tree.nodes[2]) is Line


def test_pickle_connect(canvas_fixture):
    """Persist a connection.

    """
    canvas_fixture.line.handles()[0].visible = False
    canvas_fixture.line.handles()[0].connected_to = canvas_fixture.box
    canvas_fixture.line.handles()[0].disconnect = MyDisconnect()
    canvas_fixture.line.handles()[0].connection_data = 1

    pickled = pickle.dumps(canvas_fixture.canvas)
    c2 = pickle.loads(pickled)

    assert type(canvas_fixture.canvas._tree.nodes[0]) is Box
    assert type(canvas_fixture.canvas._tree.nodes[1]) is Box
    assert type(canvas_fixture.canvas._tree.nodes[2]) is Line
    assert c2.solver

    line2 = c2._tree.nodes[2]
    h = line2.handles()[0]
    assert h.visible is False
    assert h.connected_to is c2._tree.nodes[0]

    # Connection_data and disconnect have not been persisted
    assert h.connection_data == 1, h.connection_data
    assert h.disconnect, h.disconnect
    assert callable(h.disconnect)
    assert h.disconnect() is None, h.disconnect()


def test_pickle_with_view(canvas_fixture):
    pickled = pickle.dumps(canvas_fixture.canvas)

    c2 = pickle.loads(pickled)

    view = View(canvas=c2)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
    cr = cairo.Context(surface)
    view.update_bounding_box(cr)
    cr.show_page()
    surface.flush()
    surface.finish()


def test_pickle_with_gtk_view(canvas_fixture):
    pickled = pickle.dumps(canvas_fixture.canvas)

    c2 = pickle.loads(pickled)

    win = Gtk.Window()
    view = GtkView(canvas=c2)
    win.add(view)

    view.show()
    win.show()

    view.update()


def test_pickle_with_gtk_view_with_connection(canvas_fixture):
    box = canvas_fixture.canvas._tree.nodes[0]
    assert isinstance(box, Box)
    line = canvas_fixture.canvas._tree.nodes[2]
    assert isinstance(line, Line)

    f = io.BytesIO()
    pickler = MyPickler(f)
    pickler.dump(canvas_fixture.canvas)
    pickled = f.getvalue()

    c2 = pickle.loads(pickled)

    win = Gtk.Window()
    view = GtkView(canvas=c2)
    win.add(view)
    view.show()
    win.show()

    view.update()


def test_pickle_demo():
    canvas = demo.create_canvas()

    pickled = pickle.dumps(canvas)

    c2 = pickle.loads(pickled)

    win = Gtk.Window()
    view = GtkView(canvas=c2)
    win.add(view)

    view.show()
    win.show()

    view.update()
