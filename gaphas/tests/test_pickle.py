#!/usr/bin/env python

# Copyright (C) 2008-2017 Arjan Molenaar <gaphor@gmail.com>
#                         Dan Yeaw <dan@yeaw.me>
#
# This file is part of Gaphas.
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Library General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Library General Public License for
# more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.

import pickle
import unittest
import toga

from gaphas.itemcontainer import ItemContainer
from gaphas.examples import Box
from gaphas.item import Element, Line
from gaphas.view import View, TogaView


# Ensure extra pickle reducers/reconstructors are loaded:
import gaphas.picklers


class MyPickler(pickle.Pickler):
    def save(self, obj):
        print('saving obj', obj, type(obj))
        try:
            return pickle.Pickler.save(self, obj)
        except pickle.PicklingError as e:
            print('Error while pickling', obj, self.dispatch.get(type(obj)))
            raise e


class my_disconnect(object):
    """
    Disconnect object should be located at top-level, so the pickle code
    can find it.
    """

    def __call__(self):
        pass


def create_item_container():
    item_container = ItemContainer()
    box = Box()
    item_container.add(box)
    box.matrix.translate(100, 50)
    box.matrix.rotate(50)
    box2 = Box()
    item_container.add(box2, parent=box)

    line = Line()
    line.handles()[0].visible = False
    line.handles()[0].connected_to = box
    line.handles()[0].disconnect = my_disconnect()
    line.handles()[0].connection_data = 1

    item_container.add(line)

    item_container.update()

    return item_container


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
        item_container = create_item_container()

        pickled = pickle.dumps(item_container)
        c2 = pickle.loads(pickled)

        assert type(item_container._tree.nodes[0]) is Box
        assert type(item_container._tree.nodes[1]) is Box
        assert type(item_container._tree.nodes[2]) is Line

    def test_pickle_connect(self):
        """
        Persist a connection.
        """
        item_container = ItemContainer()
        box = Box()
        item_container.add(box)
        box2 = Box()
        item_container.add(box2, parent=box)

        line = Line()
        line.handles()[0].visible = False
        line.handles()[0].connected_to = box
        line.handles()[0].disconnect = my_disconnect()
        line.handles()[0].connection_data = 1

        item_container.add(line)

        pickled = pickle.dumps(item_container)
        c2 = pickle.loads(pickled)

        assert type(item_container._tree.nodes[0]) is Box
        assert type(item_container._tree.nodes[1]) is Box
        assert type(item_container._tree.nodes[2]) is Line
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
        item_container = create_item_container()

        pickled = pickle.dumps(item_container)

        c2 = pickle.loads(pickled)

        view = View(item_container=c2)

        import cairo
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        cr = cairo.Context(surface)
        view.update_bounding_box(cr)
        cr.show_page()
        surface.flush()
        self.finish = surface.finish()

    def test_pickle_with_gtk_view(self):
        item_container = create_item_container()

        pickled = pickle.dumps(item_container)

        c2 = pickle.loads(pickled)

        win = toga.Window()
        view = TogaView(item_container=c2)
        view.show()
        win.show()
        view.update()

    def test_pickle_with_gtk_view_with_connection(self):
        item_container = create_item_container()
        box = item_container._tree.nodes[0]
        assert isinstance(box, Box)
        line = item_container._tree.nodes[2]
        assert isinstance(line, Line)

        view = TogaView(item_container=item_container)

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
        pickler.dump(item_container)
        pickled = f.getvalue()

        c2 = pickle.loads(pickled)

        win = toga.Window()
        view = TogaView(item_container=c2)
        view.show()
        win.show()

        view.update()

    def test_pickle_demo(self):
        import demo

        item_container = demo.create_item_container()

        pickled = pickle.dumps(item_container)

        c2 = pickle.loads(pickled)

        win = toga.Window()
        view = TogaView(item_container=c2)

        view.show()
        win.show()

        view.update()


if __name__ == '__main__':
    unittest.main()

# vim: sw=4:et:ai
