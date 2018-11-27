from __future__ import print_function

import pickle
import unittest
from builtins import object

from future import standard_library
from gi.repository import Gtk

from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Element, Line
from gaphas.view import View, GtkView

# Ensure extra pickle reducers/reconstructors are loaded:
import gaphas.picklers

standard_library.install_aliases()


class MyPickler(pickle.Pickler):
    def save(self, obj):
        # print('saving obj', obj, type(obj))
        try:
            return pickle.Pickler.save(self, obj)
        except pickle.PicklingError as e:
            print("Error while pickling", obj, self.dispatch.get(type(obj)))
            raise e


class MyDisconnect(object):
    """
    Disconnect object should be located at top-level, so the pickle code
    can find it.
    """

    def __call__(self):
        pass


def create_canvas():
    canvas = Canvas()
    box = Box()
    canvas.add(box)
    box.matrix.translate(100, 50)
    box.matrix.rotate(50)
    box2 = Box()
    canvas.add(box2, parent=box)

    line = Line()
    line.handles()[0].visible = False
    line.handles()[0].connected_to = box
    line.handles()[0].disconnect = MyDisconnect()
    line.handles()[0].connection_data = 1

    canvas.add(line)

    canvas.update()

    return canvas


class PickleTestCase(unittest.TestCase):
    def test_pickle_element(self):
        item = Element()

        pickled = pickle.dumps(item)
        i2 = pickle.loads(pickled)

        assert i2
        assert len(i2.handles()) == 4

    def test_pickle_line(self):
        item = Line()

        pickled = pickle.dumps(item)
        i2 = pickle.loads(pickled)

        assert i2
        assert len(i2.handles()) == 2

    def test_pickle(self):
        canvas = create_canvas()

        pickled = pickle.dumps(canvas)
        c2 = pickle.loads(pickled)

        assert type(canvas._tree.nodes[0]) is Box
        assert type(canvas._tree.nodes[1]) is Box
        assert type(canvas._tree.nodes[2]) is Line

    def test_pickle_connect(self):
        """
        Persist a connection.
        """
        canvas = Canvas()
        box = Box()
        canvas.add(box)
        box2 = Box()
        canvas.add(box2, parent=box)

        line = Line()
        line.handles()[0].visible = False
        line.handles()[0].connected_to = box
        line.handles()[0].disconnect = MyDisconnect()
        line.handles()[0].connection_data = 1

        canvas.add(line)

        pickled = pickle.dumps(canvas)
        c2 = pickle.loads(pickled)

        assert type(canvas._tree.nodes[0]) is Box
        assert type(canvas._tree.nodes[1]) is Box
        assert type(canvas._tree.nodes[2]) is Line
        assert c2.solver

        line2 = c2._tree.nodes[2]
        h = line2.handles()[0]
        assert h.visible == False
        assert h.connected_to is c2._tree.nodes[0]

        # connection_data and disconnect have not been persisted
        assert h.connection_data == 1, h.connection_data
        assert h.disconnect, h.disconnect
        assert callable(h.disconnect)
        assert h.disconnect() is None, h.disconnect()

    def test_pickle_with_view(self):
        canvas = create_canvas()

        pickled = pickle.dumps(canvas)

        c2 = pickle.loads(pickled)

        view = View(canvas=c2)

        import cairo

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        cr = cairo.Context(surface)
        view.update_bounding_box(cr)
        cr.show_page()
        surface.flush()
        surface.finish()

    def test_pickle_with_gtk_view(self):
        canvas = create_canvas()

        pickled = pickle.dumps(canvas)

        c2 = pickle.loads(pickled)

        win = Gtk.Window()
        view = GtkView(canvas=c2)
        win.add(view)

        view.show()
        win.show()

        view.update()

    def test_pickle_with_gtk_view_with_connection(self):
        canvas = create_canvas()
        box = canvas._tree.nodes[0]
        assert isinstance(box, Box)
        line = canvas._tree.nodes[2]
        assert isinstance(line, Line)

        view = GtkView(canvas=canvas)

        #        from gaphas.tool import ConnectHandleTool
        #        handle_tool = ConnectHandleTool()
        #        handle_tool.connect(view, line, line.handles()[0], (40, 0))
        #        assert line.handles()[0].connected_to is box, line.handles()[0].connected_to
        #        assert line.handles()[0].connection_data
        #        assert line.handles()[0].disconnect
        #        assert isinstance(line.handles()[0].disconnect, object), line.handles()[0].disconnect

        import io

        f = io.BytesIO()
        pickler = MyPickler(f)
        pickler.dump(canvas)
        pickled = f.getvalue()

        c2 = pickle.loads(pickled)

        win = Gtk.Window()
        view = GtkView(canvas=c2)
        win.add(view)
        view.show()
        win.show()

        view.update()

    def test_pickle_demo(self):
        import demo

        canvas = demo.create_canvas()

        pickled = pickle.dumps(canvas)

        c2 = pickle.loads(pickled)

        win = Gtk.Window()
        view = GtkView(canvas=c2)
        win.add(view)

        view.show()
        win.show()

        view.update()


if __name__ == "__main__":
    unittest.main()

# vim: sw=4:et:ai
