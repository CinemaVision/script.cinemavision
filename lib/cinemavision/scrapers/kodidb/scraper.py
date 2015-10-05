import datetime
from lib.kodijsonrpc import rpc


def getTrailers():
    for m in rpc.VideoLibrary.GetMovies(properties=['trailer', 'mpaa', 'genre', 'year']).get('movies', []):
        trailer = m.get('trailer')

        if not trailer:
            continue

        yield {
            'ID': m['movieid'],
            'url': trailer,
            'rating': m['mpaa'],
            'genres': m['genre'],
            'title': m['label'],
            'release': datetime.datetime(year=m.get('year') or 1900, month=1, day=1)
        }
