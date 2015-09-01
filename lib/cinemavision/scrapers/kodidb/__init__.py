import scraper


class Trailer:
    def __init__(self, data):
        self.data = data
        self.is3D = False
        if not self.data.get('rating'):
            self.data['rating'] = 'NR'

    @property
    def ID(self):
        return 'kodiDB:{0}'.format(self.data['ID'])

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
        return self.data['rating'] or 'NR'

    @property
    def ratingFormat(self):
        return 'MPAA'

    @property
    def fullRating(self):
        return '{0}:{1}'.format(self.ratingFormat, self.rating)

    @property
    def userAgent(self):
        return ''

    def getPlayableURL(self, res='720p'):
        return self.data['url']


class KodiDBTrailerRetriever:
    def getTrailers(self):
        return [Trailer(t) for t in scraper.getTrailers()]
