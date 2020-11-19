from gi.repository import Gtk

from gaphas.aspect.finder import handle_at_point, item_at_point
from gaphas.types import Pos
from gaphas.view import GtkView


def hover_tool(view: GtkView):
    ctrl = Gtk.EventControllerMotion.new(view)
    # ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    ctrl.connect("motion", on_motion, view)
    return ctrl


def on_motion(ctrl, x, y, view):
    view.selection.set_hovered_item(find_item_at_point(view, (x, y)))


def find_item_at_point(view: GtkView, pos: Pos):
    item, handle = handle_at_point(view, pos)
    return item or item_at_point(view, pos)
