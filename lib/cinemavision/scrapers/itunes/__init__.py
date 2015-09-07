import scraper
import re
import util


class Trailer:
    def __init__(self, data):
        self.data = data
        self.is3D = False
        if self.data.get('rating', '').lower().startswith('not'):
            self.data['rating'] = 'NR'

    @property
    def ID(self):
        return 'itunes:{0}'.format(self.data['location'])

    @property
    def title(self):
        return self.data['title']

    @property
    def thumb(self):
        return self.data['poster']

    @property
    def genres(self):
        return re.split(' and |, ', self.data.get('genre', ''))

    @property
    def rating(self):
        return self.data['rating']

    @property
    def ratingFormat(self):
        return 'MPAA'

    @property
    def fullRating(self):
        return '{0}:{1}'.format(self.ratingFormat, self.rating)

    @property
    def userAgent(self):
        return scraper.USER_AGENT

    def getPlayableURL(self, res='720p'):
        try:
            return self._getPlayableURL(res)
        except:
            util.ERROR()

        return None

    def _getPlayableURL(self, res='720p'):
        ts = scraper.TrailerScraper()
        all_ = [t for t in ts.get_trailers(self.data['location']) if t]

        if not all_:
            return None

        try:
            versions = [t for t in all_ if t['title'] == 'Trailer']
        except IndexError:
            versions = all_

        version = None
        try:
            version = [v for v in versions if any(res in u for u in v['urls'])][0]
            if version:
                return [u for u in version['urls'] if res in u][0]
        except:
            import traceback
            traceback.print_exc()

        try:
            return versions[0]['urls'][0]
        except:
            import traceback
            traceback.print_exc()

        return None


class ItunesTrailerRetriever:
    def getTrailers(self):
        ms = scraper.MovieScraper()
        return [Trailer(t) for t in ms.get_most_recent_movies(None)]
