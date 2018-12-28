
Gaphas vs jHotDraw
------------------

Gaphas || jHotDraw
Item    | Figure
Canvas  | Drawing
Tool    | Tool
Painter | Painter
View    | DrawingView

jHotDraw let's you enable one tool at a time. In Gaphas everything should be
handled from within one tool chain. Tool chains can be switched, e.g. for
specific actions such as item placement. Everything else (item, handle
manupilation, zooming, selection) is handled without the need to select
specific tools.

Items (Figures in jHotDraw) keep track of their own child items. In Gaphas, the
Canvas object maintains the hierarchical order of items. Advantage is that
addition of items is never unnoticed. Also iterating the nodes in the tree
structure is a bit faster.

In jHotDraw, connections of items (figures) are maintained within the special
connection figure. Gaphas maintains connections between items as constraints
and uses a constraint solver (one per canvas) to ensure the constraints remain
true.


