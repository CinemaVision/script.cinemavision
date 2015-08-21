import scraper


class Trailer:
    def __init__(self, data):
        self.data = data
        self.is3D = True

    @property
    def ID(self):
        return 'stereoscopynews:{0}'.format(self.data['ID'])

    @property
    def title(self):
        return self.data['title']

    @property
    def thumb(self):
        return self.data['poster']

    @property
    def genres(self):
        return []

    @property
    def rating(self):
        return 'NR'

    @property
    def ratingFormat(self):
        return 'MPAA'

    @property
    def fullRating(self):
        return '{0}:{1}'.format(self.ratingFormat, self.rating)

    @property
    def userAgent(self):
        return None

    def getPlayableURL(self, res='720p'):
        return 'plugin://plugin.video.youtube/play/?video_id={0}'.format(self.data['ID'])


class StereoscopyNewsTrailerRetriever:
    def getMovies(self):
        return [Trailer(t) for t in scraper.getTrailers()]
