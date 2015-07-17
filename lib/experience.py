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
    "dtsma":     "DTS-HD",
    "dtshd_ma":  "DTS-HD",
    "dtshd_hra": "DTS-HD",
    "dtshr":     "DTS-HD",
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
                feature.audioFormat = AUDIO_FORMATS.get(r['streamdetails']['audio'][0]['codec'])
            except:
                pass

            self.processor.addFeature(feature)

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
            if self.processor.empty() or not self.window.isOpen:
                break
        self.log('[ -- Finished -------------------------------------------------------------- ]')
        self.window.doClose()

    def showImage(self, image):
        kodiutil.setGlobalProperty('slide', image.path)

        start = time.time()
        while not kodiutil.wait(0.1) and time.time() - start < image.duration:
            if not self.window.isOpen:
                self.abort()
                break

        kodiutil.setGlobalProperty('slide', '')
        self.next()

    def showVideo(self, video):
        path = video.path

        if video.userAgent:
            path += '|User-Agent=' + video.userAgent

        self.play(path)

    def next(self):
        if self.processor.empty():
            return

        if not self.window.isOpen:
            self.abort()
            return

        playable = self.processor.next()
        if not playable:
            self.window.doClose()
            return

        self.log('Playing next item: {0}'.format(playable))

        if playable.type == 'IMAGE':
            self.showImage(playable)
        elif playable.type in ('VIDEO', 'FEATURE'):
            self.showVideo(playable)
        else:
            self.log('NOT PLAYING: {0}'.format(playable))
            self.next()

    def abort(self):
        self.log('ABORT')
        self.window.doClose()
