""" Item and Handle.
"""

class Handle(object):
    
    def __init__(self, pos=(0,0)):
        self._pos = pos
    
    pos = property(lambda s: s._pos)

    def update(self, context):
        """Update the handle. @context has the following attributes:
         - item: the owning item
         - matrix_i2w: Item to World transformation matrix
        """
        pass


class Item(object):

    def __init__(self, canvas=None):
        self._canvas = canvas
        self.dirty = True

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

    def render(self, context):
        """Render the item to a canvas view.
        Context contains the following attributes:
         - canvas: the owning canvas
         - matrix_i2w: Item to World transformation matrix (no need to)
         - cairo: the Cairo Context use this one to draw.
        """
        pass

    def handles(self):
        """Return an iterator for the handles owned by the item.
        """
        return iter()


