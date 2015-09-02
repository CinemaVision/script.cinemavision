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
        path = kodiutil.getSetting('sequence.3D')
    else:
        path = kodiutil.getSetting('sequence.2D')

    if path:
        return path

    return defaultSavePath()


def getDBPath(from_load=False):
    dbPath = None
    if not kodiutil.getSetting('content.path'):
        dbPath = os.path.join(kodiutil.PROFILE_PATH, 'demo')
        if not os.path.exists(dbPath):
            copyDemoContent()
            downloadDemoContent()
            if not from_load:
                loadContent()
        return dbPath
    return None


def loadContent():
    from cinemavision import content

    contentPath = kodiutil.getSetting('content.path')
    dbPath = getDBPath(from_load=True)
    if not contentPath:
        contentPath = os.path.join(kodiutil.PROFILE_PATH, 'demo')

    kodiutil.DEBUG_LOG('Loading content...')

    with kodiutil.Progress('Loading Content') as p:
        return content.UserContent(contentPath, callback=p.msg, db_path=dbPath)


def downloadDemoContent():
    import xbmc
    import requests
    import zipfile
    url = 'http://cinemavision.tv/cvdemo/Demo.zip'
    output = os.path.join(kodiutil.PROFILE_PATH, 'demo.zip')
    target = os.path.join(kodiutil.PROFILE_PATH, 'demo', 'Trivia Slides')
    # if not os.path.exists(target):
    #     os.makedirs(target)

    with open(output, 'wb') as handle:
        response = requests.get(url, stream=True)
        total = float(response.headers.get('content-length', 1))
        sofar = 0
        blockSize = 4096
        if not response.ok:
            return False

        with kodiutil.Progress('Download', 'Downloading demo content') as p:
            for block in response.iter_content(blockSize):
                sofar += blockSize
                pct = int((sofar/total) * 100)
                p.update(pct)
                handle.write(block)

    z = zipfile.ZipFile(output)
    z.extractall(target)
    xbmc.sleep(500)
    try:
        os.remove(output)
    except:
        kodiutil.ERROR()

    return True


def copyDemoContent():
    source = os.path.join(kodiutil.ADDON_PATH, 'resources', 'demo')
    dest = os.path.join(kodiutil.PROFILE_PATH, 'demo')
    import shutil
    shutil.copytree(source, dest)
