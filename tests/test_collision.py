from gaphas.collision import colliding_lines
from gaphas.connections import Connections
from gaphas.item import Element, Item, Line
from gaphas.quadtree import Quadtree


def test_colliding_lines():
    connections = Connections()
    qtree: Quadtree[Item, None] = Quadtree()

    line = Line(connections=connections)
    line.head.pos = (0, 50)
    line.tail.pos = (200, 50)

    element = Element(connections=connections)
    element.height = 100
    element.width = 100
    element.matrix.translate(50, 0)

    qtree.add(line, (0, 50, 200, 50))
    qtree.add(element, (50, 0, 150, 100))

    collisions = list(colliding_lines(qtree))

    assert (line, element) in collisions
