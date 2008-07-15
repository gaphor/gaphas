
import unittest
import pickle
from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Item, Element, Line


class my_disconnect(object):
    """
    Disconnect object should be located at top-level, so the pickle code
    can find it.
    """
    def __call__(self):
        pass


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
        canvas = Canvas()
        box = Box()
        canvas.add(box)
        box2 = Box()
        canvas.add(box2, parent=box)

        line = Line()
        canvas.add(line)

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
        line.handles()[0].disconnect = my_disconnect()
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


# vim: sw=4:et:ai
