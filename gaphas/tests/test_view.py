#!/usr/bin/env python

# Copyright (C) 2007-2017 Arjan Molenaar <gaphor@gmail.com>
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

"""
Test cases for the View class.
"""

import math
import unittest

import toga

from gaphas.canvas import Canvas
from gaphas.examples import Box
from gaphas.item import Line
from gaphas.view import View, TogaView


class ViewTestCase(unittest.TestCase):
    def test_bounding_box_calculations(self):
        """
        A view created before and after the canvas is populated should contain
        the same data.
        """
        canvas = Canvas()

        window1 = toga.Window()
        view1 = TogaView(canvas=canvas)
        view1.realize()
        window1.show()

        box = Box()
        box.matrix = (1.0, 0.0, 0.0, 1, 10, 10)
        canvas.add(box)

        line = Line()
        line.fyzzyness = 1
        line.handles()[1].pos = (30, 30)
        # line.split_segment(0, 3)
        line.matrix.translate(30, 60)
        canvas.add(line)

        window2 = toga.Window()
        view2 = TogaView(canvas=canvas)
        window2.show()

        # Process pending (expose) events, which cause the canvas to be drawn.
        # while Gtk.events_pending():
        #     Gtk.main_iteration()

        try:
            assert view2.get_item_bounding_box(box)
            assert view1.get_item_bounding_box(box)
            assert view1.get_item_bounding_box(box) == view2.get_item_bounding_box(box), '%s != %s' % (
                view1.get_item_bounding_box(box), view2.get_item_bounding_box(box)
            )
            assert view1.get_item_bounding_box(line) == view2.get_item_bounding_box(line), '%s != %s' % (
                view1.get_item_bounding_box(line), view2.get_item_bounding_box(line)
            )
        finally:
            window1.destroy()
            window2.destroy()

    def test_get_item_at_point(self):
        """
        Hover tool only reacts on motion-notify events
        """
        canvas = Canvas()
        window = toga.Window()
        view = TogaView(canvas)
        window.show()

        box = Box()
        canvas.add(box)
        # No gtk main loop, so updates occur instantly
        assert not canvas.require_update()
        box.width = 50
        box.height = 50

        # Process pending (expose) events, which cause the canvas to be drawn.
        # while Gtk.events_pending():
        #     Gtk.main_iteration()

        assert len(view._qtree._ids) == 1
        assert not view._qtree._bucket.bounds == (0, 0, 0, 0), view._qtree._bucket.bounds

        assert view.get_item_at_point((10, 10)) is box
        assert view.get_item_at_point((60, 10)) is None

        window.destroy()

    def test_get_handle_at_point(self):
        canvas = Canvas()
        window = toga.Window()
        view = TogaView(canvas)
        window.show()

        box = Box()
        box.min_width = 20
        box.min_height = 30
        box.matrix.translate(20, 20)
        box.matrix.rotate(math.pi / 1.5)
        canvas.add(box)

        i, h = view.get_handle_at_point((20, 20))
        assert i is box
        assert h is box.handles()[0]

    def test_get_handle_at_point_at_pi_div_2(self):
        canvas = Canvas()
        window = toga.Window()
        view = TogaView(canvas)
        window.show()

        box = Box()
        box.min_width = 20
        box.min_height = 30
        box.matrix.translate(20, 20)
        box.matrix.rotate(math.pi / 2)
        canvas.add(box)

        p = canvas.get_matrix_i2c(box).transform_point(0, 20)
        p = canvas.get_matrix_c2i(box).transform_point(20, 20)
        i, h = view.get_handle_at_point((20, 20))
        assert i is box
        assert h is box.handles()[0]

    def test_item_removal(self):
        canvas = Canvas()
        window = toga.Window()
        view = TogaView(canvas)
        window.show()

        box = Box()
        canvas.add(box)
        # No gtk main loop, so updates occur instantly
        assert not canvas.require_update()

        # Process pending (expose) events, which cause the canvas to be drawn.
        # while Gtk.events_pending():
        #     Gtk.main_iteration()

        assert len(canvas.get_all_items()) == len(view._qtree)

        view.focused_item = box
        canvas.remove(box)

        assert len(canvas.get_all_items()) == 0
        assert len(view._qtree) == 0

        window.destroy()

    def test_view_registration(self):
        canvas = Canvas()

        # Simple views do not register on the canvas

        view = View(canvas)
        assert len(canvas._registered_views) == 0

        box = Box()
        canvas.add(box)

        # By default no complex updating/calculations are done:
        assert view not in box._matrix_i2v
        assert view not in box._matrix_v2i

        # GTK view does register for updates though

        view = TogaView(canvas)
        assert len(canvas._registered_views) == 1

        # No entry, since GtkView is not realized and has no window
        assert view not in box._matrix_i2v
        assert view not in box._matrix_v2i

        window = toga.Window()
        window.show()

        # Now everything is realized and updated
        assert view in box._matrix_i2v
        assert view in box._matrix_v2i

        view.canvas = None
        assert len(canvas._registered_views) == 0

        assert view not in box._matrix_i2v
        assert view not in box._matrix_v2i

        view.canvas = canvas
        assert len(canvas._registered_views) == 1

        assert view in box._matrix_i2v
        assert view in box._matrix_v2i

    def test_view_registration_2(self):
        """
        Test view registration and destroy when view is destroyed.
        """
        canvas = Canvas()
        window = toga.Window()
        view = TogaView(canvas)
        window.show()

        box = Box()
        canvas.add(box)

        assert hasattr(box, '_matrix_i2v')
        assert hasattr(box, '_matrix_v2i')

        assert box._matrix_i2v[view]
        assert box._matrix_v2i[view]

        assert len(canvas._registered_views) == 1
        assert view in canvas._registered_views

        window.destroy()

        assert len(canvas._registered_views) == 0

        assert view not in box._matrix_i2v
        assert view not in box._matrix_v2i

    def test_scroll_adjustments(self):
        sc = toga.ScrollContainer()
        view = TogaView(Canvas())
        sc.add(view)

        print(sc.get_hadjustment(), view.hadjustment)
        assert sc.get_hadjustment() is view.hadjustment
        assert sc.get_vadjustment() is view.vadjustment


if __name__ == '__main__':
    unittest.main()

# vim:sw=4:et:ai
