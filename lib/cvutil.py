import os
import kodiutil
from cinemavision import util


def defaultSavePath():
    return os.path.join(kodiutil.ADDON_PATH, 'resources', 'script.cinemavision.default.cvseq')


def lastSavePath():
    name = kodiutil.getSetting('save.name', '')
    path = kodiutil.getSetting('save.path', '')

    if not name or not path:
        return None

    return util.pathJoin(path, name + '.cvseq')


def getSequencePath(for_3D=False):
    if for_3D:
        path = kodiutil.getSetting('sequence.2D')
    else:
        path = kodiutil.getSetting('sequence.3D')

    if path:
        return path

    return defaultSavePath()
