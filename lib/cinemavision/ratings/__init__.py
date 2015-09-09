import util
import database as DB
from _ratings import getRatingsSystem
from _ratings import getRating
from _ratings import addRatingSystemFromXML
from _ratings import RATINGS_SYSTEMS
from _ratings import MPAA
from _ratings import RatingSystem
from _ratings import Rating
from _ratings import getRegExs


import os
import inspect

getRatingsSystem
getRating
MPAA
getRegExs


def loadFromXML():
    systemsFolder = os.path.join(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])), 'systems')
    for p in os.listdir(systemsFolder):
        path = os.path.join(systemsFolder, p)

        with open(path, 'r') as f:
            addRatingSystemFromXML(f.read())

    util.DEBUG_LOG('Rating Systems:')


def loadFromDB():
    for system in DB.RatingSystem.select():
        if system.name in RATINGS_SYSTEMS:
            RATINGS_SYSTEMS[system.name].addRegEx(system.context, system.regEx)
        else:
            rs = RatingSystem()
            rs.name = system.name
            rs.addRegEx(system.context, system.regEx)
            RATINGS_SYSTEMS[system.name] = rs

    for rating in DB.Rating.select():
        if rating.system not in RATINGS_SYSTEMS:
            continue
        RATINGS_SYSTEMS[rating.system].addRating(Rating(rating.name, rating.value, rating.internal))


def load():
    DB.initialize()
    loadFromXML()
    loadFromDB()

    for rs in RATINGS_SYSTEMS.values():
        util.DEBUG_LOG('  {0}'.format(repr(rs)))


load()
