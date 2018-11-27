from builtins import range
from os import getenv

import unittest

from gaphas.canvas import Canvas
from gaphas.examples import Box

from gaphas.item import NW, NE, SE, SW


class ElementTestCase(unittest.TestCase):
    def test_creation_with_size(self):
        """
        Test if initial size holds when added to a canvas.
        """
        canvas = Canvas()
        box = Box(150, 153)

        assert box.width == 150, box.width
        assert box.height == 153, box.height
        assert box.handles()[SE].pos.x == 150, box.handles()[SE].pos.x
        assert box.handles()[SE].pos.y == 153, box.handles()[SE].pos.y

        canvas.add(box)

        assert box.width == 150, box.width
        assert box.height == 153, box.height
        assert box.handles()[SE].pos.x == 150, box.handles()[SE].pos.x
        assert box.handles()[SE].pos.y == 153, box.handles()[SE].pos.y

    def test_resize_se(self):
        """
        Test resizing of element by dragging it SE handle.
        """
        canvas = Canvas()
        box = Box()
        handles = box.handles()

        canvas.add(box)

        h_nw, h_ne, h_se, h_sw = handles
        assert h_nw is handles[NW]
        assert h_ne is handles[NE]
        assert h_sw is handles[SW]
        assert h_se is handles[SE]

        # to see how many solver was called:
        # GAPHAS_TEST_COUNT=3 nosetests -s --with-prof
        # --profile-restrict=gaphas gaphas/tests/test_element.py | grep -e
        # '\<solve\>' -e dirty

        count = getenv("GAPHAS_TEST_COUNT")
        if count:
            count = int(count)
        else:
            count = 1

        for i in range(count):
            h_se.pos.x += 100  # h.se.{x,y} = 10, now
            h_se.pos.y += 100
            box.request_update()
            canvas.update()

        self.assertEqual(
            110 * count, h_se.pos.x
        )  # h_se changed above, should remain the same
        self.assertEqual(110 * count, float(h_se.pos.y))

        self.assertEqual(110 * count, float(h_ne.pos.x))
        self.assertEqual(110 * count, float(h_sw.pos.y))

    def test_minimal_se(self):
        """
        Test resizing of element by dragging it SE handle.
        """
        canvas = Canvas()
        box = Box()
        handles = box.handles()

        canvas.add(box)

        h_nw, h_ne, h_se, h_sw = handles
        assert h_nw is handles[NW]
        assert h_ne is handles[NE]
        assert h_sw is handles[SW]
        assert h_se is handles[SE]

        h_se.pos.x -= 20  # h.se.{x,y} == -10
        h_se.pos.y -= 20
        assert h_se.pos.x == h_se.pos.y == -10

        box.request_update()
        canvas.update()

        self.assertEqual(10, h_se.pos.x)  # h_se changed above, should be 10
        self.assertEqual(10, h_se.pos.y)

        self.assertEqual(10, h_ne.pos.x)
        self.assertEqual(10, h_sw.pos.y)


# vim:sw=4:et:ai
