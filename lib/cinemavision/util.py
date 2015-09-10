import os

DEBUG = True

STORAGE_PATH = None


def getSep(path):
    if '\\' not in path:
        return '/'
    if '/' not in path:
        return '\\'
    if path.rindex('\\') > path.rindex('/'):
        return '\\'
    return '/'


def _getSettingDefault(key):
    defaults = {
        'feature.count': 1,
        'feature.ratingBumper': 'video',
        'feature.ratingStyleSelection': 'style',
        'feature.ratingStyle': 'Classic',
        'trivia.format': 'slide',
        'trivia.duration': 10,
        'trivia.qDuration': 8,
        'trivia.cDuration': 6,
        'trivia.aDuration': 6,
        'trivia.sDuration': 10,
        'trivia.transition': 'fade',
        'trivia.transitionDuration': 400,
        'trivia.musicFile': '',
        'trivia.musicDir': '',
        'trailer.source': 'itunes',
        'trailer.count': 1,
        'trailer.limitRating': True,
        'trailer.limitGenre': True,
        'trailer.quality': '720p',
        'trailer.dir': '',
        'trailer.file': '',
        'audioformat.method': 'af.detect',
        'audioformat.fallback': 'af.format',
        'audioformat.file': '',
        'audioformat.format': 'Other',
        # Non-sequence defualts
        'bumper.fallback2D': False,
        'trivia.music': 'content',
        'trivia.musicVolume': 75,
        'trivia.musicFadeIn': 3.0,
        'trivia.musicFadeOut': 3.0,
        'trailer.playUnwatched': True
    }

    return defaults.get(key)

try:
    import xbmcvfs
    import xbmc
    import xbmcaddon
    import stat
    import time

    STORAGE_PATH = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')

    class VFS:
        def __getattr__(self, attr):
            return getattr(xbmcvfs, attr)

        def listdir(self, path):
            lists = xbmcvfs.listdir(path)
            return lists[0] + lists[1]

        class File(xbmcvfs.File):
            def __init__(self, *args, **kwargs):
                xbmcvfs.File.__init__(self)
                self._size = self.size()  # size() returns size at open, so we need to keep track ourselves
                self._pos = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                self.close()

            def flush(self):
                pass

            def tell(self):
                return self._pos

            def read(self, nbytes=-1):
                self._pos += nbytes
                if self._pos >= self._size or not nbytes:
                    self._pos = self._size - 1
                return xbmcvfs.File.read(self, nbytes)

            def write(self, data):
                self._pos += len(data)
                self._size = max(self._pos, self._size)
                return xbmcvfs.File.write(self, data)

            def seek(self, offset, whence=0):
                if whence == 0:
                    self._pos = 0
                elif whence == 2:
                    self._pos = self._size - 1
                self._pos += offset
                return xbmcvfs.File.seek(self, offset, whence)

    vfs = VFS()

    def pathJoin(*args):
        args = list(args)
        sep = getSep(args[0])
        ret = [args.pop(0).rstrip('/\\')]
        for a in args:
            ret.append(a.strip('/\\'))
        return sep.join(ret)

    def isDir(path):
        vstat = xbmcvfs.Stat(path)
        return stat.S_ISDIR(vstat.st_mode())

    def LOG(msg):
        xbmc.log('[- CinemaVison -] (API): {0}'.format(msg))

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

    def getSettingDefault(key):
        default = xbmcaddon.Addon().getSetting(key)

        if default == '':
            return _getSettingDefault(key)

        if key == 'trailer.source':
            return ['itunes', 'kodidb', 'dir', 'file'][int(default)]
        elif key == 'trivia.format':
            return ['slide', 'video'][int(default)]
        elif key == 'trivia.music':
            return ['off', 'content', 'dir', 'file'][int(default)]
        elif key == 'audioformat.method':
            return ['af.detect', 'af.format', 'af.file'][int(default)]
        elif key == 'audioformat.fallback':
            return ['af.format', 'af.file'][int(default)]
        elif key == 'trivia.transition':
            return ['none', 'fade', 'slideL', 'slideR', 'slideU', 'slideD'][int(default)]
        elif key == 'audioformat.format':
            return [
                'Auro-3D', 'Dolby Digital', 'Dolby Digital Plus', 'Dolby TrueHD',
                'Dolby Atmos', 'DTS', 'DTS-HD Master Audio', 'DTS-X', 'Datasat', 'THX', 'Other'
            ][int(default)]
        elif key == 'trailer.globalRatingLimit':
            import ratings
            return [None, ratings.MPAA.G, ratings.MPAA.PG, ratings.MPAA.PG_13, ratings.MPAA.R, ratings.MPAA.NC_17][int(default)]
        elif key == 'feature.ratingBumper':
            return ['none', 'video', 'image'][int(default)]
        elif key == 'feature.ratingStyleSelection':
            return ['random', 'style'][int(default)]
        elif default in ['true', 'false']:
            return default == 'true'
        elif default.isdigit():
            return int(default)

        try:
            return float(default)
        except ValueError:
            pass

        return default

    videoExtensions = tuple(xbmc.getSupportedMedia('video').split('|') + ['.cvurl'])
    musicExtensions = tuple(xbmc.getSupportedMedia('music').split('|'))
    imageExtensions = tuple(xbmc.getSupportedMedia('picture').split('|'))

except:
    raise
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

    def getSettingDefault(key):
        return _getSettingDefault(key)

    videoExtensions = ('.mp4',)
    musicExtensions = ('.mp3', '.wav')
    imageExtensions = ('.jpg', '.png')


def listFilePaths(path):
    ret = []
    for f in vfs.listdir(path):
        full = pathJoin(path, f)
        if not isDir(full):
            ret.append(full)
    return ret


def datetimeTotalSeconds(td):
    return float((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)) / 10**6


def DEBUG_LOG(msg):
    if DEBUG:
        LOG(msg)


def ERROR(msg=None):
    if msg:
        LOG(msg)
    import traceback
    traceback.print_exc()
