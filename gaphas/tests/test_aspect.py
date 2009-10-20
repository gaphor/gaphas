"""
Generic gaphas item tests.
"""

import unittest

from gaphas.item import Item
from gaphas.aspect import Aspect, aspectfactory, aspect
from gaphas.aspect import Selection, InMotion
from gaphas.canvas import Canvas, Context
from gaphas.view import View
from gaphas.tool import ToolContext

class AspectTestCase(unittest.TestCase):
    """
    Test aspects for items.
    """

    def setUp(self):
        self.canvas = Canvas()
        self.view = View(self.canvas)

    def test_aspect_decorator(self):
        class A(object): pass
        class B(A): pass
        class C(A): pass

        @aspectfactory
        class MyAspect(Aspect):
            def __init__(self, item, arg2, arg3):
                self.item, self.arg2, self.arg3 = item, arg2, arg3
        @aspect(A)
        class A_Aspect(MyAspect):
            pass
        @aspect(B)
        class B_Aspect(MyAspect):
            pass

        a = A()
        asp = MyAspect(a, 1, 2)
        assert asp.item is a
        assert asp.arg2 == 1
        assert asp.arg3 == 2

        b =B()
        asp = MyAspect(b, 1, 2)    # doctest: +ELLIPSIS
        assert asp.item is b
        assert asp.arg2 == 1
        assert asp.arg3 == 2

        @aspect(B)
        @aspectfactory
        class CustomAspect(Aspect):
            def __init__(self, item):
                self.item = item
    
        b = B()
        asp = CustomAspect(b)      # doctest: +ELLIPSIS
        assert asp.item is b

        asp = MyAspect(b, 1, 2)    # doctest: +ELLIPSIS
        assert asp.item is b
        assert asp.arg2 == 1
        assert asp.arg3 == 2


    def test_selection_select(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        selection = Selection(item, view)
        assert item not in view.selected_items
        selection.select()
        assert item in view.selected_items
        assert item is view.focused_item
        selection.unselect()
        assert item not in view.selected_items
        assert None is view.focused_item


    def test_selection_move(self):
        """
        Test the Selection role methods
        """
        view = self.view
        item = Item()
        self.canvas.add(item)
        inmotion = InMotion(item, view)
        self.assertEquals((1, 0, 0, 1, 0, 0), tuple(item.matrix))
        inmotion.start_move(x=0, y=0)
        inmotion.move(x=12, y=26)
        self.assertEquals((1, 0, 0, 1, 12, 26), tuple(item.matrix))

# vim:sw=4:et:ai
