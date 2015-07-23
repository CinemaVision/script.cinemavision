import os

DEBUG = True

STORAGE_PATH = None

CALLBACK = None

try:
    import xbmcvfs as vfs
    import xbmc
    import xbmcaddon
    import stat
    import time

    STORAGE_PATH = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')

    def pathJoin(*args):
        return xbmc.translatePath(os.path.join(*args))

    def isDir(path):
        vstat = vfs.Stat(path)
        return stat.S_ISDIR(vstat.st_mode())

    def LOG(msg):
        xbmc.log('[- CinemaVison -] (API): {0}'.format(msg))

    old_listdir = vfs.listdir

    def vfs_listdir(path):
        lists = old_listdir(path)
        return lists[0] + lists[1]

    vfs.listdir = vfs_listdir

    try:
        xbmc.Monitor().waitForAbort

        def wait(timeout):
            return xbmc.Monitor().waitForAbort(timeout)
    except:
        def wait(timeout):
            start = time.time()
            while not xbmc.abortRequested and time.time() - start < timeout:
                xbmc.sleep(100)
            return xbmc.abortRequested

except:
    import zipfile

    STORAGE_PATH = '/home/ruuk/tmp/content'

    def vfs():
        pass

    class InsideZipFile(zipfile.ZipFile):
        def __init__(self, *args, **kwargs):
            zipfile.ZipFile.__init__(self, *args, **kwargs)
            self._inner = None

        def setInner(self, inner):
            self._inner = inner

        def read(self, bytes=-1):
            return self._inner.read(bytes)

    vfs.mkdirs = os.makedirs

    def exists(path):
        if '.zip' in path:  # This would fail in an uncontrolled setting
            zippath, inpath = path.split('.zip', 1)
            zippath = zippath + '.zip'
            inpath = inpath.lstrip(os.path.sep)
            z = zipfile.ZipFile(zippath, 'r')
            try:
                z.getinfo(inpath)
                return True
            except KeyError:
                return False

        return os.path.exists(path)

    vfs.exists = exists

    def File(path, mode):
        if '.zip' in path:  # This would fail in an uncontrolled setting
            zippath, inpath = path.split('.zip', 1)
            zippath = zippath + '.zip'
            inpath = inpath.lstrip(os.path.sep)
            z = InsideZipFile(zippath, 'r')
            i = z.open(inpath)
            z.setInner(i)
            return z

        return open(path, mode)

    vfs.File = File

    def listdir(path):
        if path.lower().endswith('.zip'):
            z = zipfile.ZipFile(path, 'r')
            items = z.namelist()
            z.close()
            return items
        return os.listdir(path)

    vfs.listdir = listdir

    def pathJoin(*args):
        return os.path.join(*args)

    def isDir(path):
        return os.path.isdir(path)

    def LOG(msg):
        print '[- CinemaVison -] (API): {0}'.format(msg)

    def wait(timeout):
        time.sleep(timeout)
        return False


def DEBUG_LOG(msg):
    if DEBUG:
        LOG(msg)


def ERROR(msg=None):
    if msg:
        LOG(msg)
    import traceback
    traceback.print_exc()


def callback(msg=None, heading=None):
    DEBUG_LOG(msg or heading)

    if CALLBACK:
        CALLBACK(msg, heading)
