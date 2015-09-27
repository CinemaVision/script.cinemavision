import datetime


class Trailer:
    @property
    def ID(self):
        return ''

    @property
    def title(self):
        return ''

    @property
    def thumb(self):
        return ''

    @property
    def genres(self):
        return []

    @property
    def userAgent(self):
        return ''

    @property
    def release(self):
        return datetime.date(1900, 1, 1)

    def getStaticURL(self):
        return None

    def getPlayableURL(self, res='720p'):
        return ''


class Scraper:
    @staticmethod
    def getPlayableURL(ID, res='720p', url=None):
        return url

    def getTrailers(self):
        return []

    def updateTrailers(self):
        return self.getTrailers()
