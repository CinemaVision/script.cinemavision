import os
from ... import util
from .. import _scrapers


def getTrailers():
    path = util.pathJoin(_scrapers.CONTENT_PATH, 'Trailers')

    if not path:
        return []

    try:
        files = util.vfs.listdir(path)
        ret = []
        for p in files:
            title, ext = os.path.splitext(p)
            if ext.lower() in util.videoExtensions:
                ret.append({'url': util.pathJoin(path, p), 'ID': p, 'title': title})
        return ret
    except:
        util.ERROR()
        return []
