""" Item and Handle.
"""

from geometry import Matrix
from solver import solvable

class Handle(object):
    """Handles are used to support modifications of Items.
    """

    x = solvable()
    y = solvable()

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        # Flags.. can't have enough of those
        self._connectable = True
        self._movable = True
        self._visible = True

    def _set_pos(self, pos):
        self.x, self.y = pos

    pos = property(lambda s: (s.x, s.y), _set_pos)

#    def update(self, context):
#        """Update the handle. @context has the following attributes:
#         - item: the owning item
#         - matrix_i2w: Item to World transformation matrix
#        """
#        pass


class Item(object):

    def __init__(self):
        self._canvas = None
        self._matrix = Matrix()

    def _set_canvas(self, canvas):
        assert not canvas or not self._canvas or self._canvas is canvas
        if self._canvas:
            self.teardown_canvas()
        self._canvas = canvas
        if canvas:
            self.setup_canvas()

    def _del_canvas(self):
        self._canvas = None

    canvas = property(lambda s: s._canvas, _set_canvas, _del_canvas)

    def setup_canvas(self):
        pass

    def teardown_canvas(self):
        pass

    def _set_matrix(self, matrix):
        if not isinstance(matrix, Matrix):
            matrix = Matrix(*matrix)
        self._matrix = matrix

    matrix = property(lambda s: s._matrix, _set_matrix)

    def request_update(self):
        if self._canvas:
            self._canvas.request_update(self)

    def pre_update(self, context):
        """Do small things that have to be done before the "real" update.
        Context has the following attributes:
         - canvas: the owning canvas
         - matrix_i2w: Item to World transformation matrix
         - ... (do I need something for text processing?)
        """
        pass


    def update(self, context):
        """Like pre_update(), but this is step 2.
        """
        pass

    def draw(self, context):
        """Render the item to a canvas view.
        Context contains the following attributes:
         - matrix_i2w: Item to World transformation matrix (no need to)
         - cairo: the Cairo Context use this one to draw.
	 - view: the view that is to be rendered to
	 - selected, focused, hovered: view state of items.
        """
        pass

    def handles(self):
        """Return an iterator for the handles owned by the item.
        """
        return iter([])

    def point(self, context, x, y):
        """Get the distance from a point (@x, @y) to the item.
	@x and @y are in item coordinates.
        Context contains the following attributes:
         - matrix_i2w: Item to World transformation matrix (no need to)
         - cairo: the Cairo Context use this one to draw.
	"""
	pass
