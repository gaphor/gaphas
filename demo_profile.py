#!/usr/bin/env python

import pygtk
pygtk.require('2.0') 

import sys
import math
import gtk
from gaphas import Canvas, GtkView, View
from gaphas.examples import Box, Text, DefaultExampleTool
from gaphas.item import Line, NW, SE
from gaphas.tool import PlacementTool, HandleTool
from gaphas.painter import ItemPainter
from gaphas import state
from gaphas.util import text_extents

from demo import *


if __name__ == '__main__':
    try:
        import cProfile
        import pstats
        cProfile.run('main()', 'demo-gaphas.prof')
        p = pstats.Stats('demo-gaphas.prof')
        p.strip_dirs().sort_stats('time').print_stats(40)
    except ImportError, ex:
        import hotshot, hotshot.stats
        import gc
        prof = hotshot.Profile('demo-gaphas.prof')
        prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load('demo-gaphas.prof')
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)

# vim: sw=4:et:
