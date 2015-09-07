import os
import re
import time
import threading

import xbmc
import xbmcgui

from kodijsonrpc import rpc

import kodigui
import kodiutil
from cinemavision import sequenceprocessor

AUDIO_FORMATS = {
    "dts":       "DTS",
    "dca":       "DTS",
    "dtsma":     "DTS-HD Master Audio",
    "dtshd_ma":  "DTS-HD Master Audio",
    "dtshd_hra": "DTS-HD Master Audio",
    "dtshr":     "DTS-HD Master Audio",
    "ac3":       "Dolby Digital",
    "eac3":      "Dolby Digital Plus",
    "a_truehd":  "Dolby TrueHD",
    "truehd":    "Dolby TrueHD"
}

TAGS_3D = '3DSBS|3D.SBS|HSBS|H.SBS|H-SBS| SBS |FULL-SBS|FULL.SBS|FULLSBS|FSBS|HALF-SBS|3DTAB|3D.TAB|HTAB|H.TAB|3DOU|3D.OU|3D.HOU| HOU | OU |HALF-TAB'


def isURLFile(path):
    if path and path.endswith('.cvurl'):
        return True
    return False


def resolveURLFile(path):
    import YDStreamExtractor as StreamExtractor

    StreamExtractor.overrideParam('noplaylist', True)
    StreamExtractor.generateBlacklist(('.*:(?:user|channel|search)$', '(?i)generic.*'))

    import xbmcvfs
    f = xbmcvfs.File(path, 'r')
    try:
        url = f.read().strip()
    except:
        kodiutil.ERROR()
        return
    finally:
        f.close()

    vid = StreamExtractor.getVideoInfo(url)

    if not vid:
        return None

    return vid.streamURL()

RATING_REs = (
    ('MPAA', r'(?i)^Rated\s(?P<rating>Unrated|NR|PG-13|PG|G|R|NC-17)'),
    ('BBFC', r'(?i)^UK(?:\s+|:)(?P<rating>Uc|U|12A|12|PG|15|R18|18)'),
    ('FSK', r'(?i)^(?:FSK|Germany)(?:\s+|:)(?P<rating>0|6|12|16|18|Unrated)'),
    ('DEJUS', r'(?i)(?P<rating>Livre|10 Anos|12 Anos|14 Anos|16 Anos|18 Anos)')
)


def getActualRatingFromMPAA(rating):
    if not rating:
        return 'MPAA:NA'

    for system, ratingRE in RATING_REs:
        m = re.search(ratingRE, rating)
        if m:
            return '{0}:{1}'.format(system, m.group('rating'))

    return 'MPAA:NA'


class KodiVolumeControl:
    def __init__(self, abort_flag):
        self.saved = None
        self.abortFlag = abort_flag
        self._stopFlag = False
        self._fader = None

    def current(self):
        return rpc.Application.GetProperties(properties=['volume'])['volume']

    def fading(self):
        if not self._fader:
            return False

        return self._fader.isAlive()

    def _set(self, volume):
        xbmc.executebuiltin("XBMC.SetVolume({0})".format(volume))
        # rpc.Application.SetVolume(volume=volume)  # This works but displays the volume indicator :(

    def store(self):
        if self.saved:
            return

        self.saved = self.current()

    def restore(self, delay=0):
        if self.saved is None:
            return

        if delay:
            xbmc.sleep(delay)

        kodiutil.DEBUG_LOG('Restoring volume to: {0}'.format(self.saved))

        self._set(self.saved)
        self.saved = None

    def set(self, volume_or_pct, fade_time=0, relative=False):
        self.store()
        if relative:
            volume = int(self.saved * (volume_or_pct / 100.0))
            kodiutil.DEBUG_LOG('Setting volume to: {0} ({1}%)'.format(volume, volume_or_pct))
        else:
            volume = volume_or_pct
            kodiutil.DEBUG_LOG('Setting volume to: {0}'.format(volume))

        if fade_time:
            current = self.current()
            self._fade(current, volume, fade_time)
        else:
            self._set(volume)

    def stop(self):
        self._stopFlag = True

    def _stop(self):
        if self._stopFlag:
            self._stopFlag = False
            return True
        return False

    def _fade(self, start, end, fade_time_millis):
        if self.fading():
            self.stop()
            self._fader.join()
        self._fader = threading.Thread(target=self._fadeWorker, args=(start, end, fade_time_millis))
        self._fader.start()

    def _fadeWorker(self, start, end, fade_time_millis):
        mod = end > start and 1 or -1
        steps = range(start, end + mod, mod)
        count = len(steps)
        if not count:
            return

        interval = fade_time_millis / count

        kodiutil.DEBUG_LOG('Fade: START ({0}) - {1}ms'.format(start, fade_time_millis))
        for step in steps:
            if xbmc.abortRequested or not xbmc.getCondVisibility('Player.Playing') or self.abortFlag.isSet() or self._stop():
                kodiutil.DEBUG_LOG(
                    'Fade ended early({0}): {1}'.format(step, not xbmc.getCondVisibility('Player.Playing') and 'NOT_PLAYING' or 'ABORT')
                )
                # self._set(end)
                return
            xbmc.sleep(interval)
            self._set(step)

        kodiutil.DEBUG_LOG('Fade: END ({0})'.format(step))


class ScreensaverControl:
    def __init__(self):
        self._originalMode = None
        self.store()

    def disable(self):
        rpc.Settings.SetSettingValue(setting='screensaver.mode', value='')
        kodiutil.DEBUG_LOG('Screensaver: DISABLED')

    def store(self):
        self._originalMode = rpc.Settings.GetSettingValue(setting='screensaver.mode').get('value')
        kodiutil.DEBUG_LOG('Screensaver: Mode stored ({0})'.format(self._originalMode))

    def restore(self):
        if not self._originalMode:
            return
        rpc.Settings.SetSettingValue(setting='screensaver.mode', value=self._originalMode)
        kodiutil.DEBUG_LOG('Screensaver: RESTORED')


class ExperienceWindow(kodigui.BaseWindow):
    xmlFile = 'script.cinemavision-experience.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    def __init__(self, *args, **kwargs):
        kodigui.BaseWindow.__init__(self, *args, **kwargs)
        self.action = None
        self.volume = None
        self.abortFlag = None
        self.effect = None
        self.duration = 400
        self.lastImage = ''
        self.initialized = False
        self.clear()

    def onInit(self):
        self.image = (self.getControl(100), self.getControl(101))
        self.initialized = True

    def join(self):
        while not kodiutil.wait(0.1) and not self.abortFlag.isSet():
            if self.initialized:
                return

    def setImage(self, url):
        if not self.effect:
            return

        if self.effect == 'none':
            self.none(url)
        elif self.effect == 'fade':
            self.change(url)
        elif self.effect == 'fadesingle':
            self.change(url)
        elif self.effect.startswith('slide'):
            self.change(url)

    def none(self, url):
        self.lastImage = url
        kodiutil.setGlobalProperty('image0', url)

    # def fade(self, url):
    #     kodiutil.setGlobalProperty('image{0}'.format(self.currentImage), url)
    #     self.currentImage = int(not self.currentImage)
    #     kodiutil.setGlobalProperty('show1', not self.currentImage and '1' or '')

    def change(self, url):
        kodiutil.setGlobalProperty('image0', self.lastImage)
        kodiutil.setGlobalProperty('show1', '')
        xbmc.sleep(100)
        kodiutil.setGlobalProperty('image1', url)
        kodiutil.setGlobalProperty('show1', '1')
        self.lastImage = url

    def clear(self):
        self.currentImage = 0
        self.lastImage = ''
        kodiutil.setGlobalProperty('image0', '')
        kodiutil.setGlobalProperty('image1', '')
        kodiutil.setGlobalProperty('show1', '')

    def setTransition(self, effect=None, duration=400):
        self.duration = duration
        self.effect = effect or 'none'
        if self.effect == 'none':
            self.image[1].setAnimations([])
        elif self.effect == 'fade':
            self.image[1].setAnimations([
                ('Visible', 'effect=fade start=0 end=100 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=fade start=100 end=0 time=0')
            ])
        elif self.effect == 'fadesingle':  # Used for single image fade in/out
            self.image[1].setAnimations([
                ('Visible', 'effect=fade start=0 end=100 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=fade start=100 end=0 time={duration}'.format(duration=self.duration))
            ])
        elif self.effect == 'slideL':
            self.image[1].setAnimations([
                ('Visible', 'effect=slide start=1980,0 end=0,0 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=slide start=0,0 end=1980,0 time=0')
            ])
        elif self.effect == 'slideR':
            self.image[1].setAnimations([
                ('Visible', 'effect=slide start=-1980,0 end=0,0 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=slide start=0,0 end=-1980,0 time=0')
            ])
        elif self.effect == 'slideU':
            self.image[1].setAnimations([
                ('Visible', 'effect=slide start=0,1080 end=0,0 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=slide start=0,0 end=0,1080 time=0')
            ])
        elif self.effect == 'slideD':
            self.image[1].setAnimations([
                ('Visible', 'effect=slide start=0,-1080 end=0,0 time={duration}'.format(duration=self.duration)),
                ('Hidden', 'effect=slide start=0,0 end=-1080 time=0')
            ])

    def fadeOut(self):
        kodiutil.setGlobalProperty('show1', '')

    def onAction(self, action):
        # print action.getId()
        try:
            if action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK or action == xbmcgui.ACTION_STOP:
                self.volume.stop()
                self.abortFlag.set()
                self.doClose()
            elif action == xbmcgui.ACTION_MOVE_RIGHT:
                if self.action != 'SKIP':
                    self.action = 'NEXT'
            elif action == xbmcgui.ACTION_MOVE_LEFT:
                if self.action != 'BACK':
                    self.action = 'PREV'
            elif action == xbmcgui.ACTION_PAGE_UP or action == xbmcgui.ACTION_NEXT_ITEM:
                self.action = 'SKIP'
            elif action == xbmcgui.ACTION_PAGE_DOWN or action == xbmcgui.ACTION_PREV_ITEM:
                self.action = 'BACK'
        except:
            kodiutil.ERROR()
            return kodigui.BaseWindow.onAction(self, action)

        kodigui.BaseWindow.onAction(self, action)

    def hasAction(self):
        return bool(self.action)

    def getAction(self):
        action = self.action
        self.action = None
        return action

    def skip(self):
        if self.action == 'SKIP':
            self.action = None
            return True
        return False

    def back(self):
        if self.action == 'BACK':
            self.action = None
            return True
        return False

    def next(self):
        if self.action == 'NEXT':
            self.action = None
            return True
        return False

    def prev(self):
        if self.action == 'PREV':
            self.action = None
            return True
        return False


class ExperiencePlayer(xbmc.Player):
    NOT_PLAYING = 0
    PLAYING_DUMMY_NEXT = -1
    PLAYING_DUMMY_PREV = -2
    PLAYING_MUSIC = -10

    DUMMY_FILE_PREV = 'script.cinemavision.dummy_PREV.mp4'
    DUMMY_FILE_NEXT = 'script.cinemavision.dummy_NEXT.mp4'

    def create(self, from_editor=False):
        # xbmc.Player.__init__(self)
        self.fromEditor = from_editor
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.fakeFilePrev = os.path.join(kodiutil.ADDON_PATH, 'resources', 'videos', 'script.cinemavision.dummy_PREV.mp4')
        self.fakeFileNext = os.path.join(kodiutil.ADDON_PATH, 'resources', 'videos', 'script.cinemavision.dummy_NEXT.mp4')
        self.featureStub = os.path.join(kodiutil.ADDON_PATH, 'resources', 'videos', 'script.cinemavision.feature_stub.mp4')
        self.playStatus = 0
        self.hasFullscreened = False
        self.has3D = False
        self.init()
        return self

    def doPlay(self, item, listitem=None, windowed=None, startpos=None):
        self.playStatus = self.NOT_PLAYING
        self.play(item)

    # PLAYER EVENTS
    def onPlayBackEnded(self):
        if self.playStatus == self.PLAYING_MUSIC:
            self.log('MUSIC ENDED')
            return
        elif self.playStatus == self.NOT_PLAYING:
            return self.onPlayBackFailed()

        self.playStatus = self.NOT_PLAYING

        if self.playlist.getposition() != -1:
            self.log('PLAYBACK ENDED')
            if self.playlist.size():
                return

        self.next()

    def onPlayBackPaused(self):
        self.log('PLAYBACK PAUSED')

    def onPlayBackResumed(self):
        self.log('PLAYBACK RESUMED')

    def onPlayBackStarted(self):
        if self.playStatus == self.PLAYING_MUSIC:
            kodiutil.DEBUG_LOG('MUSIC STARTED')
            return

        self.playStatus = time.time()
        if self.DUMMY_FILE_PREV in self.getPlayingFile():
            self.playStatus = self.PLAYING_DUMMY_PREV
            self.stop()
            return
        elif self.DUMMY_FILE_NEXT in self.getPlayingFile():
            self.playStatus = self.PLAYING_DUMMY_NEXT
            self.stop()
            return
        else:
            self.hasFullscreened = False

        self.log('PLAYBACK STARTED')

    def onPlayBackStopped(self):
        if self.playStatus == self.PLAYING_MUSIC:
            self.log('MUSIC STOPPED')
            return
        elif self.playStatus == self.NOT_PLAYING:
            return self.onPlayBackFailed()
        elif self.playStatus == self.PLAYING_DUMMY_NEXT:
            self.playStatus = self.NOT_PLAYING
            self.log('PLAYBACK INTERRUPTED')
            self.next()
            return
        elif self.playStatus == self.PLAYING_DUMMY_PREV:
            self.playStatus = self.NOT_PLAYING
            self.log('SKIP BACK')
            self.next(prev=True)
            return

        self.playStatus = self.NOT_PLAYING
        self.log('PLAYBACK STOPPED')
        self.abort()

    def onPlayBackFailed(self):
        self.playStatus = self.NOT_PLAYING
        self.log('PLAYBACK FAILED')
        self.next()

    def getPlayingFile(self):
        if self.isPlaying():
            try:
                return xbmc.Player.getPlayingFile(self)
            except RuntimeError:
                pass
            return ''
        return ''

    def init(self):
        self.abortFlag = threading.Event()
        self.window = None
        self.volume = KodiVolumeControl(self.abortFlag)
        self.screensaver = ScreensaverControl()
        self.features = []

        result = rpc.Playlist.GetItems(playlistid=xbmc.PLAYLIST_VIDEO, properties=['file', 'genre', 'mpaa', 'streamdetails', 'title', 'thumbnail', 'runtime'])
        for r in result.get('items', []):
            feature = sequenceprocessor.Feature(r['file'])
            feature.title = r.get('title') or r.get('label', '')
            ratingString = getActualRatingFromMPAA(r.get('mpaa', ''))
            if ratingString:
                feature.rating = ratingString
            feature.genres = r.get('genre', [])
            feature.thumb = r.get('thumbnail', '')
            feature.runtime = r.get('runtime', '')

            try:
                stereomode = r['streamdetails']['video'][0]['stereomode']
            except:
                stereomode = ''

            if stereomode not in ('mono', ''):
                feature.is3D = True
            else:
                feature.is3D = bool(re.findall(TAGS_3D, r['file']))

            self.has3D = self.has3D or feature.is3D

            try:
                codec = r['streamdetails']['audio'][0]['codec']
                feature.audioFormat = AUDIO_FORMATS.get(codec)
                self.log('CODEC ({0}): {1}'.format(repr(feature.title), codec))
            except:
                self.log('CODEC ({0}): NOT DETECTED'.format(repr(feature.title)))

            self.features.append(feature)

        if self.fromEditor and not self.features:
            feature = sequenceprocessor.Feature(self.featureStub)
            feature.title = 'Feature Stub'
            feature.rating = 'MPAA:PG-13'
            feature.audioFormat = 'Dolby Digital'

            self.features.append(feature)

    def addSelectedFeature(self):
        title = xbmc.getInfoLabel('ListItem.Title')
        if not title:
            return False
        feature = sequenceprocessor.Feature(xbmc.getInfoLabel('ListItem.FileNameAndPath'))
        feature.title = title

        ratingString = getActualRatingFromMPAA(xbmc.getInfoLabel('ListItem.Mpaa'))
        if ratingString:
            feature.rating = ratingString

        feature.genres = xbmc.getInfoLabel('ListItem.Genre').split(' / ')
        feature.thumb = xbmc.getInfoLabel('ListItem.Thumb')

        try:
            feature.runtime = int(xbmc.getInfoLabel('ListItem.Duration')) * 60
        except TypeError:
            pass

        feature.is3D = xbmc.getCondVisibility('ListItem.IsStereoscopic')

        if not feature.is3D:
            feature.is3D = bool(re.findall(TAGS_3D, feature.path))

        codec = xbmc.getInfoLabel('ListItem.AudioCodec')
        if codec:
            feature.audioFormat = AUDIO_FORMATS.get(codec)
            self.log('CODEC ({0}): {1}'.format(repr(feature.title), codec))
        else:
            self.log('CODEC ({0}): NOT DETECTED'.format(repr(feature.title)))

        self.features.append(feature)
        return True

    def hasFeatures(self):
        return bool(self.features)

    def playVideos(self, paths):
        self.playlist.clear()
        rpc.Playlist.Clear(playlistid=xbmc.PLAYLIST_VIDEO)

        self.playlist.add(self.fakeFilePrev)
        for path in paths:
            self.playlist.add(path)
        self.playlist.add(self.fakeFileNext)
        rpc.Player.Open(item={'playlistid': xbmc.PLAYLIST_VIDEO, 'position': 1})
        xbmc.sleep(100)
        while not xbmc.getCondVisibility('VideoPlayer.IsFullscreen') and not xbmc.abortRequested and not self.abortFlag.isSet() and self.isPlaying():
            xbmc.sleep(100)
        self.hasFullscreened = True
        kodiutil.DEBUG_LOG('VIDEO HAS GONE FULLSCREEN')

    def isPlayingMinimized(self):
        # print '{0} {1}'.format(self.isPlayingVideo(), xbmc.getCondVisibility('Player.Playing'))
        if not xbmc.getCondVisibility('Player.Playing'):  # isPlayingVideo() returns True before video actually plays (ie. is fullscreen)
            return False

        if self.playStatus <= 0:
            return False

        if xbmc.getCondVisibility('Window.IsVisible(busydialog)'):
            return False

        if time.time() - self.playStatus < 5 and not self.hasFullscreened:  # Give it a few seconds to make sure fullscreen has happened
            return False

        if not xbmc.getCondVisibility('VideoPlayer.IsFullscreen'):
            xbmc.sleep(500)

        print '{0} {1} {2} {3} {4}'.format(
            self.isPlayingVideo(),
            xbmc.getCondVisibility('Player.Playing'),
            self.playStatus,
            xbmc.getCondVisibility('VideoPlayer.IsFullscreen'),
            xbmcgui.getCurrentWindowId()
        )

        return not xbmc.getCondVisibility('VideoPlayer.IsFullscreen')

    def start(self, sequence_path):
        kodiutil.setGlobalProperty('running', '1')
        xbmcgui.Window(10025).setProperty('CinemaExperienceRunning', 'True')
        try:
            return self._start(sequence_path)
        finally:
            kodiutil.setGlobalProperty('running', '')
            xbmcgui.Window(10025).setProperty('CinemaExperienceRunning', '')

    def _start(self, sequence_path):
        import cvutil
        dbPath = cvutil.getDBPath()

        self.processor = sequenceprocessor.SequenceProcessor(sequence_path, db_path=dbPath)
        [self.processor.addFeature(f) for f in self.features]

        self.log('[ -- Started --------------------------------------------------------------- ]')

        self.openWindow()
        self.processor.process()
        self.next()
        self.waitLoop()

        del self.window
        self.window = None

    def log(self, msg):
        kodiutil.DEBUG_LOG('Experience: {0}'.format(msg))

    def openWindow(self):
        self.window = ExperienceWindow.create()
        self.window.volume = self.volume
        self.window.abortFlag = self.abortFlag
        self.window.join()

    def waitLoop(self):
        while not kodiutil.wait(0.1):
            if self.processor.atEnd() or not self.window.isOpen:
                break

            if self.isPlayingMinimized():
                self.log('Fullscreen video closed - stopping')
                self.stop()

        self.log('[ -- Finished -------------------------------------------------------------- ]')
        self.window.doClose()
        rpc.Playlist.Clear(playlistid=xbmc.PLAYLIST_VIDEO)
        self.stop()

    def playMusic(self, image_queue):
        if not image_queue.music:
            return

        pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        pl.clear()
        for s in image_queue.music:
            pl.add(s.path)

        xbmc.sleep(100)  # Without this, it will sometimes not play anything

        kodiutil.DEBUG_LOG('Playing music playlist: {0} song(s)'.format(len(pl)))

        self.volume.store()
        self.volume.set(1)

        self.playStatus = self.PLAYING_MUSIC
        self.play(pl, windowed=True)

        self.waitForPlayStart()  # Wait playback so fade will work
        self.volume.set(image_queue.musicVolume, fade_time=int(image_queue.musicFadeIn*1000), relative=True)

    def stopMusic(self, image_queue=None):
        try:
            rpc.Playlist.Clear(playlistid=xbmc.PLAYLIST_MUSIC)

            if image_queue and image_queue.music:
                self.volume.set(1, fade_time=int(image_queue.musicFadeOut*1000))
                while self.volume.fading() and not self.abortFlag.isSet() and not kodiutil.wait(0.1):
                    if self.window.hasAction():
                        break

            self.stop()
            self.waitForPlayStop()
            self.playStatus = self.NOT_PLAYING
        finally:
            self.volume.restore(delay=500)

    def waitForPlayStart(self, timeout=10000):
        giveUpTime = time.time() + timeout/1000.0
        while not xbmc.getCondVisibility('Player.Playing') and time.time() < giveUpTime and not self.abortFlag.isSet():
            xbmc.sleep(100)

    def waitForPlayStop(self):
        while self.isPlaying() and not self.abortFlag.isSet():
            xbmc.sleep(100)

    def showImage(self, image):
        try:
            if image.fade:
                self.window.setTransition('fadesingle', image.fade)

            self.window.setImage(image.path)

            stop = time.time() + image.duration
            fadeStop = image.fade and stop - (image.fade/1000) or 0

            while not kodiutil.wait(0.1) and time.time() < stop:
                if fadeStop and time.time() >= fadeStop:
                    self.window.fadeOut()

                if not self.window.isOpen:
                    return False
                elif self.window.action:
                    if self.window.next():
                        return 'NEXT'
                    elif self.window.prev():
                        return 'PREV'
                    elif self.window.skip():
                        return 'SKIP'
                    elif self.window.back():
                        return 'BACK'

            return True
        finally:
            self.window.clear()

    def showImageFromQueue(self, image, first=None, image_queue=None, music_end=None):
        self.window.setImage(image.path)

        stop = time.time() + image.duration

        while not kodiutil.wait(0.1) and time.time() < stop:
            if not self.window.isOpen:
                return False

            if music_end and time.time() >= music_end:
                music_end = None
                self.stopMusic(image_queue)

            elif self.window.action:
                if self.window.next():
                    return 'NEXT'
                elif self.window.prev():
                    return 'PREV'
                elif self.window.skip():
                    return 'SKIP'
                elif self.window.back():
                    return 'BACK'

        return True

    def showImageQueue(self, image_queue):
        image_queue.reset()
        image = image_queue.next()

        start = time.time()
        end = time.time() + image_queue.duration
        musicEnd = end - image_queue.musicFadeOut

        self.window.setTransition('none')

        xbmc.enableNavSounds(False)
        self.screensaver.disable()

        self.playMusic(image_queue)
        self.window.setTransition(image_queue.transition, image_queue.transitionDuration)

        try:
            while image:
                self.log(' -IMAGE.QUEUE: {0}'.format(image))

                action = self.showImageFromQueue(image, first=True, image_queue=image_queue, music_end=musicEnd)

                if action:
                    if action == 'NEXT':
                        image = image_queue.next(extend=True) or image
                        continue
                    elif action == 'PREV':
                        image = image_queue.prev() or image
                        continue
                    elif action == 'BACK':
                        self.log(' -IMAGE.QUEUE: Skipped after {0}secs'.format(int(time.time() - start)))
                        return False
                    elif action == 'SKIP':
                        self.log(' -IMAGE.QUEUE: Skipped after {0}secs'.format(int(time.time() - start)))
                        return True
                    else:
                        if action is True:
                            image_queue.mark(image)

                        image = image_queue.next(start)
                else:
                    return
        finally:
            self.screensaver.restore()
            xbmc.enableNavSounds(True)
            self.stopMusic(action != 'BACK' and image_queue or None)
            if self. window.hasAction():
                if self.window.getAction() == 'BACK':
                    return False
            self.window.clear()

        self.log(' -IMAGE.QUEUE: Finished after {0}secs'.format(int(time.time() - start)))
        return True

    def showVideoQueue(self, video_queue):
        pl = []
        for v in video_queue.queue:
            pl.append(v.path)
            video_queue.mark(v)

        self.playVideos(pl)

    def showVideo(self, video):
        path = video.path

        if isURLFile(path):
            path = resolveURLFile(path)
        else:
            if video.userAgent:
                path += '|User-Agent=' + video.userAgent

        if kodiutil.getSetting('allow.video.skip', True):
            self.playVideos([path])
            # self.play(self.playlist)
        else:
            self.play(path)

    def doAction(self, action):
        action.run()

    def next(self, prev=False):
        if self.processor.atEnd():
            return

        if not self.window.isOpen:
            self.abort()
            return

        if prev:
            playable = self.processor.prev()
        else:
            playable = self.processor.next()

        if playable is None:
            self.window.doClose()
            return

        self.log('Playing next item: {0}'.format(playable))

        if playable.type == 'IMAGE':
            try:
                action = self.showImage(playable)
            finally:
                self.window.clear()

            if action == 'BACK':
                self.next(prev=True)
            else:
                self.next()

        elif playable.type == 'IMAGE.QUEUE':
            if not self.showImageQueue(playable):
                self.next(prev=True)
            else:
                self.next()

        elif playable.type == 'VIDEO.QUEUE':
            self.showVideoQueue(playable)

        elif playable.type in ('VIDEO', 'FEATURE'):
            self.showVideo(playable)

        elif playable.type == 'ACTION':
            self.doAction(playable)
            self.next()

        else:
            self.log('NOT PLAYING: {0}'.format(playable))
            self.next()

    def abort(self):
        self.abortFlag.set()
        self.log('ABORT')
        self.window.doClose()
