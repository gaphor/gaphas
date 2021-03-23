import time

from gi.repository import Gtk

from gaphas import Canvas, Element, GtkView
from gaphas.painter import FreeHandPainter, HandlePainter, ItemPainter, PainterChain


class timer:
    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        self.end = time.time()
        self.print()

    def print(self):
        print(f"{self.label}: {(self.end - self.start) * 1000:.3f} ms")


class Box(Element):
    def draw(self, context):
        cr = context.cairo
        for i in range(20):
            cr.rectangle(i, i, 10, 10)
            cr.stroke()


def setup_canvas_and_view(n_boxes=20):
    canvas = Canvas()
    view = GtkView()

    boxes = [Box(canvas.connections) for i in range(n_boxes)]

    for box in boxes:
        canvas.add(box)

    painter = FreeHandPainter(ItemPainter(view.selection))
    view.painter = PainterChain().append(painter).append(HandlePainter(view))
    view.bounding_box_painter = painter
    view.model = canvas

    window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
    window.add(view)
    view.show()
    window.show()

    return canvas, view


def perf_update(rounds, canvas, view):

    with timer("update"):
        for i in range(rounds):
            view.request_update(canvas.get_all_items())


def perf_bounding_box_speed(rounds, canvas, view):

    with timer("bounding box"):
        for i in range(rounds):
            view.update_bounding_box(canvas.get_all_items())


def perf_update_back_buffer(rounds, canvas, view):
    view.update()
    with timer("update back buffer"):
        for i in range(rounds):
            view.update_back_buffer()


if __name__ == "__main__":
    boxes = 5
    rounds = 200
    print(f"Testing {boxes} boxes for {rounds} rounds")
    perf_update(rounds, *setup_canvas_and_view(boxes))
    perf_bounding_box_speed(rounds, *setup_canvas_and_view(boxes))
    perf_update_back_buffer(rounds, *setup_canvas_and_view(boxes))
