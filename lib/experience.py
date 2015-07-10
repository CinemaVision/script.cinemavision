import time

import xbmc
import xbmcgui

import kodijsonrpc
import kodigui
import kodiutil
from cinemavision import sequenceprocessor


class ExperienceWindow(kodigui.BaseWindow):
    xmlFile = 'script.cinemavision-experience.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    def onAction(self, action):
        try:
            if action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
                self.doClose()
        except:
            kodiutil.ERROR()
            return kodigui.BaseWindow.onAction(self, action)

        kodigui.BaseWindow.onAction(self, action)


class ExperiencePlayer(xbmc.Player):
    def create(self, sequence_path):
        # xbmc.Player.__init__(self)
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
        self.log('PLAYBACK ENDED')
        self.next()

    def onPlayBackPaused(self):
        self.log('PLAYBACK PAUSED')

    def onPlayBackResumed(self):
        self.log('PLAYBACK RESUMED')

    def onPlayBackStarted(self):
        self.playStatus = 1
        self.log('PLAYBACK STARTED')

    def onPlayBackStopped(self):
        if self.playStatus == 0:
            return self.onPlayBackFailed()
        self.playStatus = 0
        self.log('PLAYBACK STOPPED')
        self.abort()

    def onPlayBackFailed(self):
        self.playStatus = 0
        self.log('PLAYBACK FAILED')
        self.next()

    def init(self):
        self.window = None
        self.rpc = kodijsonrpc.KodiJSONRPC()

        result = self.rpc.Playlist.GetItems(playlistid=1, properties=['file'])  # Get video playlist
        for r in result['result'].get('items', []):
            self.processor.addFeature(r['file'])

    def start(self):
        self.log('Started -----------------------')
        self.openWindow()
        self.processor.process()
        self.next()
        self.waitLoop()

    def log(self, msg):
        kodiutil.DEBUG_LOG('Experience: {0}'.format(msg))

    def openWindow(self):
        self.window = ExperienceWindow.create()

    def waitLoop(self):
        while not kodiutil.wait(0.1):
            if self.processor.empty() or not self.window.isOpen:
                break
        self.log('Finished ----------------------')
        self.window.doClose()

    def showImage(self, image):
        self.window.setProperty('slide', image.path)

        start = time.time()
        while not kodiutil.wait(0.1) and time.time() - start < image.duration:
            if not self.window.isOpen:
                self.abort()
                break

        self.window.setProperty('slide', '')
        self.next()

    def showVideo(self, video):
        self.play(video.path)

    def next(self):
        if self.processor.empty():
            return

        if not self.window.isOpen:
            self.abort()
            return

        playable = self.processor.next()
        self.log('Playing next item: {0}'.format(playable))

        if playable.type == 'IMAGE':
            self.showImage(playable)
        elif playable.type == 'VIDEO':
            self.showVideo(playable)
        else:
            self.log('NOT PLAYING: {0}'.format(playable))
            self.next()

    def abort(self):
        self.log('ABORT')
