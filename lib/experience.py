import os
import re
import time

import xbmc
import xbmcgui

import kodijsonrpc
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


class ExperienceWindow(kodigui.BaseWindow):
    xmlFile = 'script.cinemavision-experience.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    def __init__(self, *args, **kwargs):
        kodigui.BaseWindow.__init__(self, *args, **kwargs)
        self.action = None

    def onAction(self, action):
        # print action.getId()
        try:
            if action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK or action == xbmcgui.ACTION_STOP:
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
    def create(self, sequence_path):
        # xbmc.Player.__init__(self)
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.fakeFile = os.path.join(kodiutil.ADDON_PATH, 'resources', 'dummy.mp4')
        self.playStatus = 0
        self.processor = sequenceprocessor.SequenceProcessor(sequence_path)
        self.init()
        return self

    def doPlay(self, item, listitem=None, windowed=None, startpos=None):
        self.playStatus = 0
        self.play(item)

    # PLAYER EVENTS
    def onPlayBackEnded(self):
        if self.playStatus == 0:
            return self.onPlayBackFailed()
        self.playStatus = 0
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
        if self.playlist.getposition() > 0:
            self.playStatus = -1
            self.stop()
            return
        else:
            self.log('PLAYBACK STARTED')

        self.playStatus = time.time()

    def onPlayBackStopped(self):
        if self.playStatus == 0:
            return self.onPlayBackFailed()
        elif self.playStatus == -1:
            self.log('PLAYBACK INTERRUPTED')
            self.next()
            return
        elif self.playStatus == -2:
            self.log('SKIP BACK')
            self.next(prev=True)
            return
        self.playStatus = 0
        self.log('PLAYBACK STOPPED')
        self.abort()

    def onPlayBackFailed(self):
        self.playStatus = 0
        self.log('PLAYBACK FAILED')
        self.next()

    def onPlayBackSeek(self, seek_time, offset):
        if seek_time == 0:
            self.playStatus = -2
            self.stop()

    def init(self):
        self.window = None
        self.rpc = kodijsonrpc.KodiJSONRPC()

        result = self.rpc.Playlist.GetItems(playlistid=1, properties=['file', 'genre', 'mpaa', 'streamdetails', 'title'])  # Get video playlist
        for r in result['result'].get('items', []):
            feature = sequenceprocessor.Feature(r['file'])
            feature.title = r.get('title') or r.get('label', '')
            ratingSplit = r.get('mpaa', ' ').split()
            feature.rating = ratingSplit and ratingSplit[-1] or 'NR'
            feature.ratingSystem = 'MPAA'
            feature.genres = r.get('genre', [])

            try:
                stereomode = r['streamdetails']['video'][0]['stereomode']
            except:
                stereomode = ''

            if stereomode not in ('mono', ''):
                feature.is3D = True
            else:
                feature.is3D = bool(re.findall(TAGS_3D, r['file']))

            try:
                codec = r['streamdetails']['audio'][0]['codec']
                feature.audioFormat = AUDIO_FORMATS.get(codec)
                self.log('CODEC ({0}): {1}'.format(feature.title, codec))
            except:
                self.log('CODEC ({0}): NOT DETECTED'.format(feature.title))

            self.processor.addFeature(feature)

    def isPlayingMinimized(self):
        if not self.isPlayingVideo():
            return False

        if self.playStatus > 0 and time.time() - self.playStatus < 1:  # Give it a second to make sure fullscreen has happened
            return False

        return not xbmc.getCondVisibility('VideoPlayer.IsFullscreen')

    def start(self):
        self.log('[ -- Started --------------------------------------------------------------- ]')
        self.openWindow()
        self.processor.process()
        self.next()
        self.waitLoop()

    def log(self, msg):
        kodiutil.DEBUG_LOG('Experience: {0}'.format(msg))

    def openWindow(self):
        kodiutil.setGlobalProperty('slide', '')
        self.window = ExperienceWindow.create()

    def waitLoop(self):
        while not kodiutil.wait(0.1):
            if self.processor.atEnd() or not self.window.isOpen:
                break

            if self.isPlayingMinimized():
                self.log('Fullscreen video closed - stopping')
                self.stop()

        self.log('[ -- Finished -------------------------------------------------------------- ]')
        self.window.doClose()
        self.rpc.Playlist.Clear(playlistid=1)

    def showImage(self, image):
        kodiutil.setGlobalProperty('slide', image.path)

        try:
            start = time.time()
            while not kodiutil.wait(0.1) and time.time() - start < image.duration:
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
        finally:
            kodiutil.setGlobalProperty('slide', '')

        return True

    def showImageQueue(self, image_queue):
        image_queue.reset()
        image = image_queue.next()
        start = time.time()
        while image:
            self.log(' -IMAGE.QUEUE: {0}'.format(image))
            action = self.showImage(image)
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

        self.log(' -IMAGE.QUEUE: Finished after {0}secs'.format(int(time.time() - start)))
        return True

    def showVideo(self, video):
        path = video.path

        if video.userAgent:
            path += '|User-Agent=' + video.userAgent
        self.playlist.clear()
        self.rpc.Playlist.Clear(playlistid=1)

        if kodiutil.getSetting('allow.video.skip', True):
            self.playlist.add(path)
            self.playlist.add(self.fakeFile)
            self.play(self.playlist)
        else:
            self.play(path)

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

        if not playable:
            self.window.doClose()
            return

        self.log('Playing next item: {0}'.format(playable))

        if playable.type == 'IMAGE':
            action = self.showImage(playable)
            if action == 'BACK':
                self.next(prev=True)
            else:
                self.next()

        elif playable.type == 'IMAGE.QUEUE':
            if not self.showImageQueue(playable):
                self.next(prev=True)
            else:
                self.next()

        elif playable.type in ('VIDEO', 'FEATURE'):
            self.showVideo(playable)
        else:
            self.log('NOT PLAYING: {0}'.format(playable))
            self.next()

    def abort(self):
        self.log('ABORT')
        self.window.doClose()
