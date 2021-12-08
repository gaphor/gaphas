"""Allow for easily adding segments to lines."""

from cairo import ANTIALIAS_NONE
from gi.repository import Gtk

from gaphas.connector import Handle, LinePort
from gaphas.geometry import distance_point_point_fast
from gaphas.item import Line, matrix_i2i
from gaphas.model import Model
from gaphas.selection import Selection
from gaphas.solver import WEAK
from gaphas.tool.itemtool import Segment


@Segment.register(Line)  # type: ignore
class LineSegment:
    def __init__(self, item: Line, model: Model):
        self.item = item
        self.model = model

    def split(self, pos):
        item = self.item
        handles = item.handles()
        x, y = item.matrix_i2c.inverse().transform_point(*pos)
        for h1, h2 in zip(handles, handles[1:]):
            xp = (h1.pos.x + h2.pos.x) / 2
            yp = (h1.pos.y + h2.pos.y) / 2
            if distance_point_point_fast((x, y), (xp, yp)) <= 4:
                segment = handles.index(h1)
                handles, ports = self.split_segment(segment)
                return handles and handles[0]

    def split_segment(self, segment, count=2):
        """Split one item segment into ``count`` equal pieces.

        def split_segment(self, segment, count=2):
        Two lists are returned

          - list of created handles
          - list of created ports

          :Parameters:
           segment
              Segment number to split (starting from zero).
           count
              Amount of new segments to be created (minimum 2).
        """
        item = self.item
        if segment < 0 or segment >= len(item.ports()):
            raise ValueError("Incorrect segment")
        if count < 2:
            raise ValueError("Incorrect count of segments")

        def do_split(segment, count):
            handles = item.handles()
            p0 = handles[segment].pos
            p1 = handles[segment + 1].pos
            dx, dy = p1.x - p0.x, p1.y - p0.y
            new_h = Handle((p0.x + dx / count, p0.y + dy / count), strength=WEAK)
            item.insert_handle(segment + 1, new_h)

            p0 = LinePort(p0, new_h.pos)
            p1 = LinePort(new_h.pos, p1)
            item.remove_port(item.ports()[segment])
            item.insert_port(segment, p0)
            item.insert_port(segment + 1, p1)

            if count > 2:
                do_split(segment + 1, count - 1)

        do_split(segment, count)

        # force orthogonal constraints to be recreated
        item.update_orthogonal_constraints(item.orthogonal)

        self.recreate_constraints()

        self.model.request_update(item)
        handles = item.handles()[segment + 1 : segment + count]
        ports = item.ports()[segment : segment + count - 1]
        return handles, ports

    def merge_segment(self, segment, count=2):
        """Merge two (or more) item segments.

        Tuple of two lists is returned, list of deleted handles and
        list of deleted ports.

        :Parameters:
         segment
            Segment number to start merging from (starting from zero).
         count
            Amount of segments to be merged (minimum 2).
        """
        item = self.item
        if len(item.ports()) < 2:
            raise ValueError("Cannot merge line with one segment")
        if item.orthogonal and len(item.ports()) < 1 + count:
            raise ValueError("Cannot merge orthogonal line to one segment")
        if segment < 0 or segment >= len(item.ports()):
            raise ValueError("Incorrect segment")
        if count < 2 or segment + count > len(item.ports()):
            raise ValueError("Incorrect count of segments")

        # remove handle and ports which share position with handle
        deleted_handles = item.handles()[segment + 1 : segment + count]
        deleted_ports = item.ports()[segment : segment + count]
        for h in deleted_handles:
            item.remove_handle(h)
        for p in deleted_ports:
            item.remove_port(p)

        # create new port, which replaces old ports destroyed due to
        # deleted handle
        p1 = item.handles()[segment].pos
        p2 = item.handles()[segment + 1].pos
        port = LinePort(p1, p2)
        item.insert_port(segment, port)

        # force orthogonal constraints to be recreated
        item.update_orthogonal_constraints(item.orthogonal)

        self.recreate_constraints()
        self.model.request_update(item)

        return deleted_handles, deleted_ports

    def recreate_constraints(self):
        """Create connection constraints between connecting lines and an item.

        :Parameters:
         connected
            Connected item.
        """
        connected = self.item
        model = self.model

        def find_port(line, handle, item):
            """Glue to the closest item on the canvas.

            If the item can connect, it returns a port.
            """
            pos = matrix_i2i(line, item).transform_point(*handle.pos)
            port = None
            max_dist = 10e6
            for p in item.ports():
                pg, d = p.glue(pos)
                if d >= max_dist:
                    continue
                port = p
                max_dist = d

            return port

        for cinfo in list(model.connections.get_connections(connected=connected)):
            item, handle = cinfo.item, cinfo.handle
            port = find_port(item, handle, connected)

            constraint = port.constraint(item, handle, connected)

            model.connections.reconnect_item(item, handle, port, constraint=constraint)


def segment_tool(view):
    print(
        "WARNING: You're using segment_tool(). Remove all uses of segment_tool() from your code. It's handled by item_tool now."
    )
    return (
        Gtk.GestureDrag.new(view)
        if Gtk.get_major_version() == 3
        else Gtk.GestureDrag.new()
    )


class LineSegmentPainter:
    """This painter draws pseudo-handles on gaphas.item.Line objects. Each line
    can be split by dragging those points, which will result in a new handle.

    ConnectHandleTool take care of performing the user interaction
    required for this feature.
    """

    def __init__(self, selection: Selection):
        self.selection = selection

    def paint(self, _items, cairo):
        selection = self.selection
        item = selection.hovered_item
        if isinstance(item, Line) and item is selection.focused_item:
            h = item.handles()
            for h1, h2 in zip(h[:-1], h[1:]):
                p1, p2 = h1.pos, h2.pos
                cx = (p1.x + p2.x) / 2
                cy = (p1.y + p2.y) / 2
                vx, vy = cairo.user_to_device(*item.matrix_i2c.transform_point(cx, cy))
                cairo.save()
                cairo.set_antialias(ANTIALIAS_NONE)
                cairo.identity_matrix()
                cairo.translate(vx, vy)
                cairo.rectangle(-3, -3, 6, 6)
                cairo.set_source_rgba(0, 0.5, 0, 0.4)
                cairo.fill_preserve()
                cairo.set_source_rgba(0.25, 0.25, 0.25, 0.6)
                cairo.set_line_width(1)
                cairo.stroke()
                cairo.restore()
