

def getTrailers(source=None):
    if source == 'iTunes':
        import itunes
        itunesRetriever = itunes.ItunesTrailerRetriever()
        return itunesRetriever.getTrailers()
    elif source == 'kodiDB':
        import kodidb
        kodiDBRetriever = kodidb.KodiDBTrailerRetriever()
        return kodiDBRetriever.getTrailers()


def getPlayableURL(ID, quality=None, source=None, url=None):
    if source == 'iTunes':
        import itunes
        return itunes.ItunesTrailerRetriever.getPlayableURL(ID, quality or '720p')
    elif source == 'kodiDB':
        import kodidb
        return kodidb.KodiDBTrailerRetriever.getPlayableURL(ID, url=url)
