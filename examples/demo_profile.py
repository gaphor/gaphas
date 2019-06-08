#!/usr/bin/env python

from examples.demo import *


if __name__ == "__main__":
    try:
        import cProfile
        import pstats

        cProfile.run("main()", "demo-gaphas.prof")
        p = pstats.Stats("demo-gaphas.prof")
        p.strip_dirs().sort_stats("time").print_stats(40)
    except ImportError as ex:
        import hotshot, hotshot.stats
        import gc

        prof = hotshot.Profile("demo-gaphas.prof")
        prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load("demo-gaphas.prof")
        stats.strip_dirs()
        stats.sort_stats("time", "calls")
        stats.print_stats(20)
