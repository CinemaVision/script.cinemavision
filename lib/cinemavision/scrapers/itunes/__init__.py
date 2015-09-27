import scraper
import os
import re
import time
import datetime
from ... import ratings
from ... import util
from .. import _scrapers


class Trailer(_scrapers.Trailer):
    def __init__(self, data):
        self.data = data
        self.is3D = False
        if self.data.get('rating', '').lower().startswith('not'):
            self.data['rating'] = 'NR'
        self.rating = ratings.getRating('MPAA', self.data['rating'])

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
    def userAgent(self):
        return scraper.USER_AGENT

    @property
    def release(self):
        return self.data.get('releasedatetime', datetime.date(1900, 1, 1))

    def getStaticURL(self):
        return None

    def getPlayableURL(self, res='720p'):
        try:
            return self._getPlayableURL(res)
        except:
            import traceback
            traceback.print_exc()

        return None

    def _getPlayableURL(self, res='720p'):
        return ItunesTrailerScraper(self.data['location'], res)


class ItunesTrailerScraper(_scrapers.Scraper):
    LAST_UPDATE_FILE = os.path.join(util.STORAGE_PATH, 'itunes.last')

    def __init__(self):
        self.loadTimes()

    @staticmethod
    def getPlayableURL(ID, res=None, url=None):
        res = res or '720p'

        ts = scraper.TrailerScraper()
        all_ = [t for t in ts.get_trailers(ID) if t]

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

    def loadTimes(self):
        self.lastAllUpdate = 0
        self.lastRecentUpdate = 0
        if not os.path.exists(self.LAST_UPDATE_FILE):
            return
        try:
            with open(self.LAST_UPDATE_FILE, 'r') as f:
                self.lastAllUpdate, self.lastRecentUpdate = [int(x) for x in f.read().splitlines()[:2]]
        except:
            util.ERROR()

    def saveTimes(self):
        with open(self.LAST_UPDATE_FILE, 'w') as f:
            f.write('{0}\n{1}'.format(int(self.lastAllUpdate), int(self.lastRecentUpdate)))

    def allIsDue(self):
        if time.time() - self.lastAllUpdate > 2592000:  # One month
            self.lastAllUpdate = time.time()
            self.saveTimes()
            return True
        return False

    def recentIsDue(self):
        if time.time() - self.lastRecentUpdate > 86400:  # One day
            self.lastRecentUpdate = time.time()
            self.saveTimes()
            return True
        return False

    def getTrailers(self):
        ms = scraper.MovieScraper()
        if self.allIsDue():
            util.DEBUG_LOG('    - Fetching all trailers')
            return [Trailer(t) for t in ms.get_all_movies(None)]

        return []

    def updateTrailers(self):
        ms = scraper.MovieScraper()
        if self.recentIsDue():
            util.DEBUG_LOG('    - Fetching recent trailers')
            return [Trailer(t) for t in ms.get_most_recent_movies(None)]

        return []
