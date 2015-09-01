

def getTrailers(source=None):
    if source == 'iTunes':
        import itunes
        itunesRetriever = itunes.ItunesTrailerRetriever()
        return itunesRetriever.getTrailers()
    elif source == 'kodiDB':
        import kodidb
        kodiDBRetriever = kodidb.KodiDBTrailerRetriever()
        return kodiDBRetriever.getTrailers()
