

_SOURCES = {
    'itunes': 'iTunes',
    'kodidb': 'kodiDB',
    'stereoscopynews': 'StereoscopyNews'
}


def getScraper(source=None):
    source = _SOURCES.get(source.lower().strip())

    if source == 'iTunes':
        import itunes
        return itunes.ItunesTrailerScraper()
    elif source == 'kodiDB':
        import kodidb
        return kodidb.KodiDBTrailerScraper()
    elif source == 'StereoscopyNews':
        import stereoscopynews
        return stereoscopynews.StereoscopyNewsTrailerScraper()
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
    scraper = getScraper(source)
    if not scraper:
        return None

    return scraper.getPlayableURL(ID, quality, url)
