import scraper
from lib import cvutil
import datetime
from ... import ratings


class Trailer:
    def __init__(self, data):
        self.data = data
        self.is3D = False
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
    def release(self):
        return self.data.get('releasedatetime', datetime.date(1900, 1, 1))

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

    def getStaticURL(self):
        return self.data['url']

    def getPlayableURL(self, res='720p'):
        return self.data['url']


class KodiDBTrailerRetriever:
    @staticmethod
    def getPlayableURL(ID, res=720, url=None):
        return url

    def getTrailers(self):
        return [Trailer(t) for t in scraper.getTrailers()]
