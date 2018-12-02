"""
Allow for easily adding segments to lines.
"""
from __future__ import division

from builtins import object
from builtins import zip

from cairo import Matrix, ANTIALIAS_NONE
from simplegeneric import generic

from gaphas.aspect import ConnectionSink
from gaphas.aspect import HandleFinder, HandleSelection, PaintFocused
from gaphas.aspect import ItemHandleFinder, ItemHandleSelection, ItemPaintFocused
from gaphas.geometry import distance_point_point_fast, distance_line_point
from gaphas.item import Line


@generic
class Segment(object):
    def __init__(self, item, view):
        raise TypeError


@Segment.when_type(Line)
class LineSegment(object):
    def __init__(self, item, view):
        self.item = item
        self.view = view

    def split(self, pos):
        item = self.item
        handles = item.handles()
        x, y = self.view.get_matrix_v2i(item).transform_point(*pos)
        for h1, h2 in zip(handles, handles[1:]):
            xp = (h1.pos.x + h2.pos.x) / 2
            yp = (h1.pos.y + h2.pos.y) / 2
            if distance_point_point_fast((x, y), (xp, yp)) <= 4:
                segment = handles.index(h1)
                handles, ports = self.split_segment(segment)
                return handles and handles[0]

    def split_segment(self, segment, count=2):
        """
        Split one item segment into ``count`` equal pieces.

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
            new_h = item._create_handle((p0.x + dx / count, p0.y + dy / count))
            item._reversible_insert_handle(segment + 1, new_h)

            p0 = item._create_port(p0, new_h.pos)
            p1 = item._create_port(new_h.pos, p1)
            item._reversible_remove_port(item.ports()[segment])
            item._reversible_insert_port(segment, p0)
            item._reversible_insert_port(segment + 1, p1)

            if count > 2:
                do_split(segment + 1, count - 1)

        do_split(segment, count)

        # force orthogonal constraints to be recreated
        item._update_orthogonal_constraints(item.orthogonal)

        self._recreate_constraints()

        handles = item.handles()[segment + 1 : segment + count]
        ports = item.ports()[segment : segment + count - 1]
        return handles, ports

    def merge_segment(self, segment, count=2):
        """
        Merge two (or more) item segments.

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
            raise ValueError("Cannot merge item with one segment")
        if segment < 0 or segment >= len(item.ports()):
            raise ValueError("Incorrect segment")
        if count < 2 or segment + count > len(item.ports()):
            raise ValueError("Incorrect count of segments")

        # remove handle and ports which share position with handle
        deleted_handles = item.handles()[segment + 1 : segment + count]
        deleted_ports = item.ports()[segment : segment + count]
        for h in deleted_handles:
            item._reversible_remove_handle(h)
        for p in deleted_ports:
            item._reversible_remove_port(p)

        # create new port, which replaces old ports destroyed due to
        # deleted handle
        p1 = item.handles()[segment].pos
        p2 = item.handles()[segment + 1].pos
        port = item._create_port(p1, p2)
        item._reversible_insert_port(segment, port)

        # force orthogonal constraints to be recreated
        item._update_orthogonal_constraints(item.orthogonal)

        self._recreate_constraints()

        return deleted_handles, deleted_ports

    def _recreate_constraints(self):
        """
        Create connection constraints between connecting lines and an item.

        :Parameters:
         connected
            Connected item.
        """
        connected = self.item

        def find_port(line, handle, item):
            # port = None
            # max_dist = sys.maxint
            canvas = item.canvas

            ix, iy = canvas.get_matrix_i2i(line, item).transform_point(*handle.pos)

            # find the port using item's coordinates
            sink = ConnectionSink(item, None)
            return sink.find_port((ix, iy))

        if not connected.canvas:
            # No canvas, no constraints
            return

        canvas = connected.canvas
        for cinfo in list(canvas.get_connections(connected=connected)):
            item, handle = cinfo.item, cinfo.handle
            port = find_port(item, handle, connected)

            constraint = port.constraint(canvas, item, handle, connected)

            cinfo = canvas.get_connection(handle)
            canvas.reconnect_item(item, handle, constraint=constraint)


@HandleFinder.when_type(Line)
class SegmentHandleFinder(ItemHandleFinder):
    """
    Find a handle on a line, create a new one if the mouse is located
    between two handles. The position aligns with the points drawn by
    the SegmentPainter.
    """

    def get_handle_at_point(self, pos):
        view = self.view
        item = view.hovered_item
        handle = None
        if self.item is view.focused_item:
            try:
                segment = Segment(self.item, self.view)
            except TypeError:
                pass
            else:
                handle = segment.split(pos)

        if not handle:
            item, handle = super(SegmentHandleFinder, self).get_handle_at_point(pos)
        return item, handle


@HandleSelection.when_type(Line)
class SegmentHandleSelection(ItemHandleSelection):
    """
    In addition to the default behaviour, merge segments if the handle
    is released.
    """

    def unselect(self):
        item = self.item
        handle = self.handle
        handles = item.handles()

        # don't merge using first or last handle
        if handles[0] is handle or handles[-1] is handle:
            return True

        handle_index = handles.index(handle)
        segment = handle_index - 1

        # cannot merge starting from last segment
        if segment == len(item.ports()) - 1:
            segment = -1
        assert segment >= 0 and segment < len(item.ports()) - 1

        before = handles[handle_index - 1]
        after = handles[handle_index + 1]
        d, p = distance_line_point(before.pos, after.pos, handle.pos)

        if d < 2:
            assert len(self.view.canvas.solver._marked_cons) == 0
            Segment(item, self.view).merge_segment(segment)

        if handle:
            item.request_update()


@PaintFocused.when_type(Line)
class LineSegmentPainter(ItemPaintFocused):
    """
    This painter draws pseudo-handles on gaphas.item.Line
    objects. Each line can be split by dragging those points, which
    will result in a new handle.

    ConnectHandleTool take care of performing the user interaction
    required for this feature.
    """

    def paint(self, context):
        view = self.view
        item = view.hovered_item
        if item and item is view.focused_item:
            cr = context.cairo
            h = item.handles()
            for h1, h2 in zip(h[:-1], h[1:]):
                p1, p2 = h1.pos, h2.pos
                cx = (p1.x + p2.x) / 2
                cy = (p1.y + p2.y) / 2
                cr.save()
                cr.identity_matrix()
                m = Matrix(*view.get_matrix_i2v(item))

                cr.set_antialias(ANTIALIAS_NONE)
                cr.translate(*m.transform_point(cx, cy))
                cr.rectangle(-3, -3, 6, 6)
                cr.set_source_rgba(0, 0.5, 0, 0.4)
                cr.fill_preserve()
                cr.set_source_rgba(0.25, 0.25, 0.25, 0.6)
                cr.set_line_width(1)
                cr.stroke()
                cr.restore()


# vim:sw=4:et:ai
