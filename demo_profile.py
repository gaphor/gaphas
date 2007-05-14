import demo

import hotshot, hotshot.stats
prof = hotshot.Profile('demo-gaphas.prof')
prof.runcall(demo.main)
prof.close()
stats = hotshot.stats.load('demo-gaphas.prof')
stats.strip_dirs()
stats.sort_stats('time', 'calls')
stats.print_stats(20)

