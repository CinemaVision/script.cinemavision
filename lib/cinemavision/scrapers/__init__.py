from . import _scrapers
from .. import util

_SOURCES = {
    'itunes': 'iTunes',
    'kodidb': 'kodiDB',
    'tmdb': 'TMDB',
    'content': 'Content'
}


def getScraper(source=None):
    source = _SOURCES.get(source.lower().strip())

    if source == 'iTunes':
        from . import itunes
        return itunes.ItunesTrailerScraper()
    elif source == 'kodiDB':
        from . import kodidb
        return kodidb.KodiDBTrailerScraper()
    elif source == 'Content':
        from . import content
        return content.ContentTrailerScraper()
    elif source == 'TMDB':
        from . import tmdb
        return tmdb.TMDBTrailerScraper()
    return None


def getTrailers(source=None):
    scraper = getScraper(source)
    if not scraper:
        return None

    return scraper.getTrailers()


def updateTrailers(source=None):
    scraper = getScraper(source)
    if not scraper:
        return None

    return scraper.updateTrailers()


def getPlayableURL(ID, quality=None, source=None, url=None):
    try:
        scraper = getScraper(source)
        if not scraper:
            return None
    except:
        util.ERROR()
        return None

    return scraper.getPlayableURL(ID, quality, url)


def setContentPath(path):
    _scrapers.CONTENT_PATH = path