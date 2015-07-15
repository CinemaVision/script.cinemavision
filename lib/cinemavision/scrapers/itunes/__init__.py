import scraper
import re


class Trailer:
    def __init__(self, data):
        self.data = data

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

    def getPlayableURL(self):
        ts = scraper.TrailerScraper()
        all_ = [t for t in ts.get_trailers(self.data['location'])]
        try:
            versions = [t for t in all_ if t['title'] == 'Trailer'][0]
        except IndexError:
            versions = all_

        url = [u for u in versions['urls'] if '720p' in u][0]
        if not url:
            return versions['urls'][0]

        return url


class ItunesTrailerRetriever:
    def getMovies(self):
        ms = scraper.MovieScraper()
        return [Trailer(t) for t in ms.get_most_recent_movies(None)]
