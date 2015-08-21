import itunes


def getTrailers():
    itunesRetriever = itunes.ItunesTrailerRetriever()
    return itunesRetriever.getTrailers()
