import re
import scraper
from lib import cvutil
from ... import util
from ... import ratings
from .. import _scrapers


class Trailer(_scrapers.Trailer):
    def __init__(self, data):
        self.data = data
        self._is3D = bool(re.search(util.TAGS_3D_REGEX, self.data.get('url', '')))
        if not self.data.get('rating'):
            self.data['rating'] = u'NR'

    @property
    def ID(self):
        return u'kodiDB:{0}'.format(self.data['ID'])

    @property
    def title(self):
        return self.data['title']

    @property
    def thumb(self):
        return ''

    @property
    def genres(self):
        return self.data.get('genres', [])

    @property
    def rating(self):
        if not getattr(self, '_rating', None):
            ratingString = self.data.get('rating')
            if ratingString:
                self._rating = ratings.getRating(cvutil.ratingParser().getActualRatingFromMPAA(ratingString))
            else:
                self._rating = None
        return self._rating

    @rating.setter
    def rating(self, val):
        self['rating'] = val

    @property
    def userAgent(self):
        return ''

    @property
    def is3D(self):
        return self._is3D

    def getStaticURL(self):
        return self.data['url']

    def getPlayableURL(self, res='720p'):
        return self.data['url']


class KodiDBTrailerScraper(_scrapers.Scraper):
    @staticmethod
    def getPlayableURL(ID, res=720, url=None):
        return url

    def getTrailers(self):
        return [Trailer(t) for t in scraper.getTrailers()]
