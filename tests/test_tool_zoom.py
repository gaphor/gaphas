import pytest
from gi.repository import Gtk

from gaphas.tool.zoom import ZoomData, on_begin, on_scale_changed, zoom_tool


@pytest.fixture
def zoom_data():
    zoom_data = ZoomData()
    zoom_data.x0 = 0
    zoom_data.y0 = 0
    zoom_data.sx = 1
    zoom_data.sy = 1
    return zoom_data


def test_can_create_zoom_tool(view):
    tool = zoom_tool(view)

    assert isinstance(tool, Gtk.Gesture)


def test_begin_state(zoom_data, view):
    class MockGesture:
        def get_point(self, sequence):
            return True, 1, 2

    gesture = MockGesture()
    sequence = None

    on_begin(gesture, sequence, zoom_data, view)

    assert zoom_data.x0 == 1
    assert zoom_data.y0 == 2
    assert zoom_data.sx == 1
    assert zoom_data.sy == 1


def test_scaling(zoom_data, view):
    on_scale_changed(None, 1.2, zoom_data, view)

    assert view.matrix[0] == 1.2
    assert view.matrix[3] == 1.2


def test_multiple_scaling_events(zoom_data, view):
    on_scale_changed(None, 1.1, zoom_data, view)
    on_scale_changed(None, 1.2, zoom_data, view)

    assert view.matrix[0] == 1.2
    assert view.matrix[3] == 1.2


def test_scaling_with_unequal_scaling_factor(zoom_data, view):
    zoom_data.sx = 2
    on_scale_changed(None, 1.2, zoom_data, view)

    assert view.matrix[0] == 2.4
    assert view.matrix[3] == 1.2


def test_zoom_should_center_around_mouse_cursor(zoom_data, view):
    zoom_data.x0 = 100
    zoom_data.y0 = 50

    on_scale_changed(None, 1.2, zoom_data, view)

    assert view.matrix[4] == -20.0
    assert view.matrix[5] == -10.0


def test_zoom_out_should_be_limited_to_20_percent(zoom_data, view):
    on_scale_changed(None, 0.0, zoom_data, view)

    assert view.matrix[0] == 0.2
    assert view.matrix[3] == 0.2


def test_zoom_in_should_be_limited_to_20_times(zoom_data, view):
    on_scale_changed(None, 100.0, zoom_data, view)

    assert view.matrix[0] == 20
    assert view.matrix[3] == 20
