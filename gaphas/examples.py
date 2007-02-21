"""Simple example items.
These items are used in various tests.
"""

__version__ = "$Revision$"
# $HeadURL$

from item import Handle, Element, Item
from item import NW, NE,SW, SE
from solver import solvable
import tool
from constraint import LineConstraint
from geometry import point_on_rectangle, distance_rectangle_point

class Box(Element):
    """ A Box has 4 handles (for a start):
     NW +---+ NE
     SW +---+ SE
    """
    min_width = 10
    min_height = 10
    def __init__(self, width=10, height=10):
        #super(Box, self).__init__(width, height)
        print 'Box.__init__'
        Element.__init__(self,width, height)

    def draw(self, context):
        #print 'Box.draw', self
        c = context.cairo
        nw = self._handles[NW]
        c.rectangle(nw.x, nw.y, self.width, self.height)
        if context.hovered:
            c.set_source_rgba(.8,.8,1, .8)
        else:
            c.set_source_rgba(1,1,1, .8)
        c.fill_preserve()
        c.set_source_rgb(0,0,0.8)
        c.stroke()
        context.draw_children()

    def glue(self, item, handle, x, y):
        """Special glue method used by the ConnectingHandleTool to find
        a connection point.
        """
        h = self._handles
        hnw = h[NW]
        hse = h[SE]
        r = (float(hnw.x), float(hnw.y), float(hse.x), float(hse.y))
        por = point_on_rectangle(r, (x, y), border=True)
        #print 'Point', r, (x, y), por
        return distance_rectangle_point(r, (x, y)), por


class Text(Item):
    """Simple item shoring some text on the canvas.
    """

    def __init__(self):
        super(Text, self).__init__()

    def draw(self, context):
        #print 'Text.draw', self
        c = context.cairo
        c.show_text('Hello')
        context.draw_children()

    def point(self, x, y):
        return 0


class ConnectingHandleTool(tool.HandleTool):
    """This is a HandleTool which supports a simple connection algerithm,
    Using LineConstraint.
    """

    def glue(self, view, item, handle, wx, wy):
        """It allows the tool to glue to a Box or (other) Line item.
        The distance from the item to the handle is determined in canvas
        coordinates, using a 10 pixel glue distance.
        """
        if not handle.connectable:
            return
        matrix_w2i = view.canvas.get_matrix_w2i
        matrix_i2w = view.canvas.get_matrix_i2w

        # Make glue distance depend on the zoom ratio (should be about 10 pixels)
        glue_distance, dummy = view.transform_distance_c2w(10, 0)
        glue_point = None
        glue_item = None
        for i in view.canvas.get_all_items():
            if not i is item:
                ix, iy = matrix_w2i(i).transform_point(wx, wy)
                try:
                    distance, point = i.glue(item, handle, ix, iy)
                    #print distance, point
                    # Transform distance to world coordinates
                    distance, dumy = matrix_i2w(i).transform_distance(distance, 0)
                    if distance <= glue_distance:
                        glue_distance = distance
                        glue_point = matrix_i2w(i).transform_point(*point)
                        glue_item = i
                except AttributeError:
                    pass
        if glue_point:
            handle.x, handle.y = matrix_w2i(item).transform_point(*glue_point)
        return glue_item

    def connect(self, view, item, handle, wx, wy):
        """Connect a handle to another item.

        In this "method" the following assumptios are made:
         1. The only item that accepts handle connections are the Box instances
         2. The only items with connectable handles are Line's
         
        """
        def side(handle, glued):
            hx, hy = view.canvas.get_matrix_i2w(item).transform_point(handle.x, handle.y)
            ax, ay = view.canvas.get_matrix_i2w(glued).transform_point(glued.handles()[0].x, glued.handles()[0].y)
            bx, by = view.canvas.get_matrix_i2w(glued).transform_point(glued.handles()[2].x, glued.handles()[2].y)
            if abs(hx - ax) < 0.01:
                side = 3
            elif abs(hy - ay) < 0.01:
                side = 0
            elif abs(hx - bx) < 0.01:
                side = 1
            else:
                side = 2
            return side


        def handle_disconnect():
            try:
                view.canvas.solver.remove_constraint(handle._connect_constraint)
            except KeyError:
                pass # constraint was alreasy removed
            handle._connect_constraint = None
            handle.connected_to = None
            # Remove disconnect handler:
            handle.disconnect = lambda: 0

        #print 'Handle.connect', view, item, handle, wx, wy
        glue_item = self.glue(view, item, handle, wx, wy)
        if glue_item and glue_item is handle.connected_to:
            s = side(handle, glue_item)
            try:
                view.canvas.solver.remove_constraint(handle._connect_constraint)
            except KeyError:
                pass # constraint was alreasy removed
            handle._connect_constraint = LineConstraint(view.canvas, glue_item, glue_item.handles()[s], glue_item.handles()[(s+1)%4], item, handle)
            view.canvas.solver.add_constraint(handle._connect_constraint)
            handle.disconnect = handle_disconnect
            return

        # drop old connetion
        if handle.connected_to:
            handle.disconnect()

        if glue_item:
            if isinstance(glue_item, Box):
                s = side(handle, glue_item)
                # Make a constraint that keeps into account item coordinates.
                handle._connect_constraint = LineConstraint(view.canvas, glue_item, glue_item.handles()[s], glue_item.handles()[(s+1)%4], item, handle)
                view.canvas.solver.add_constraint(handle._connect_constraint)
                handle.connected_to = glue_item
                handle.disconnect = handle_disconnect

    def disconnect(self, view, item, handle):
        if handle.connected_to:
            #print 'Handle.disconnect', view, item, handle
            view.canvas.solver.remove_constraint(handle._connect_constraint)


def DefaultExampleTool():
    """The default tool chain build from HoverTool, ItemTool and HandleTool.
    """
    chain = tool.ToolChain()
    chain.append(tool.HoverTool())
    chain.append(ConnectingHandleTool())
    chain.append(tool.ItemTool())
    chain.append(tool.TextEditTool())
    chain.append(tool.RubberbandTool())
    return chain


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: sw=4:et:ai
