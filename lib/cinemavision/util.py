DEBUG = True

try:
    import xbmcvfs as vfs
    import xbmc
    import stat

    def pathJoin(p1, p2):
        return xbmc.validatePath(p1 + '/' + p2)

    def isDir(path):
        vstat = vfs.stat(path)
        return stat.S_ISDIR(vstat.st_mode())

    def LOG(msg):
        xbmc.log('CinemaVison (API): {0}'.format(msg))

except:
    import os
    import zipfile

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

    vfs.makedirs = os.makedirs

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

    def pathJoin(p1, p2):
        return os.path.join(p1, p2)

    def isDir(path):
        return os.path.isdir(path)

    def LOG(msg):
        print 'CinemaVison (API): {0}'.format(msg)


def DEBUG_LOG(msg):
    if DEBUG:
        LOG(msg)


def ERROR(msg=None):
    if msg:
        LOG(msg)
    import traceback
    traceback.print_exc()
