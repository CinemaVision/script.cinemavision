import util
from _ratings import getRatingsSystem
from _ratings import getRating
from _ratings import addRatingSystemFromXML
from _ratings import RATINGS_SYSTEMS
from _ratings import MPAA

import os
import inspect

getRatingsSystem
getRating
MPAA

systemsFolder = os.path.join(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])), 'systems')
for p in os.listdir(systemsFolder):
    path = os.path.join(systemsFolder, p)

    with open(path, 'r') as f:
        addRatingSystemFromXML(f.read())

util.DEBUG_LOG('Rating Systems:')

for rs in RATINGS_SYSTEMS.values():
    util.DEBUG_LOG('  {0}'.format(repr(rs)))
