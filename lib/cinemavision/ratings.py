class RatingSystem:
    name = ''
    ratings = []

    @classmethod
    def getRatingByName(cls, name):
        name = name.upper()
        for r in cls.ratings:
            if r.name == name:
                return r
        return NO_RATING


class Rating:
    system = ''

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ne__(self, other):
        return self.value != other.value


class MPAA(RatingSystem):
    class MPAARating(Rating):
        system = 'MPAA'

    NC_17 = MPAARating('NC-17', 170)
    R = MPAARating('R', 160)
    PG_13 = MPAARating('PG-13', 130)
    PG = MPAARating('PG', 120)
    G = MPAARating('G', 0)
    NR = MPAARating('NR', 1000)

    name = 'MPAA'
    ratings = [NR, G, PG, PG_13, R, NC_17]


RATINGS_SYSTEMS = {
    'MPAA': MPAA
}


NO_RATING = Rating('', 100)


def getRatingsSystem(name):
    name = name.upper()
    return RATINGS_SYSTEMS.get(name)


def getRating(system, name=None):
    if not name:
        if ':' in system:
            system, name = system.split(':', 1)
        else:
            return NO_RATING

    system = getRatingsSystem(system)
    if not system:
        return NO_RATING

    return system.getRatingByName(name)
