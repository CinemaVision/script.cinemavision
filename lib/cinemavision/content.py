import util

import os
import re
from xml.etree import ElementTree as ET


class ContentBase:
    _type = 'BASE'
    _subType = None

    def __str__(self):
        return '<{0}:{1}>'.format(self.typeID, self.name)

    def __repr__(self):
        return self.__str__()

    @property
    def typeID(self):
        if self._subType:
            return '.'.join((self._type, self._subType))
        return self._type


class Song(ContentBase):
    _type = 'song'

    def __init__(self):
        self.name = ''
        self.path = ''


class Trivia(ContentBase):
    _type = 'trivia'
    _subType = 'fact'

    def __init__(self, slide_path=''):
        self.name = ''
        self.rating = ''
        self.slidePath = slide_path


class TriviaQA(Trivia):
    _subType = 'QA'

    def __init__(self, question_path=''):
        Trivia.__init__(self)
        self.name = ''
        self.rating = ''
        self.questionPath = question_path
        self.cluePaths = []
        self.answerPath = ''

    def addCluePath(self, path):
        self.cluePaths.append(path)


class Bumper(ContentBase):
    _type = 'bumpers'

    def __init__(self, name):
        self.name = name
        self.bumpers = []
        self.bumpers3D = []

    def add(self, path):
        if '3D' in path:
            self.bumpers3D.append(path)
        else:
            self.bumpers.append(path)


class AudioFormat(Bumper):
    _subType = 'audio.format'

    def __init__(self, format_):
        Bumper.__init__(self, format_)
        self.format = format_


class Ratings(Bumper):
    _subType = 'ratings'

    def __init__(self, system):
        Bumper.__init__(self, system)
        self.system = system


class CinemaSpot(ContentBase):
    _type = 'spot'

    def __init__(self, type_):
        self.name = type_
        self.type = type_
        self.spots = []
        self.spots3D = []

    def add(self, path):
        if '3D' in path:
            self.spots3D.append(path)
        else:
            self.spots.append(path)


class UserContent:
    _tree = (
        'Music',
        'Trivia',
        ('Videos', (
            ('Audio Format Bumpers', (
                'Auro 3D Audio Bumpers',
                'Dolby Atmos Bumpers',
                'Dolby Digital Bumpers',
                'Dolby Digital Plus Bumpers',
                'Dolby TrueHD Bumpers',
                'DTS Bumpers',
                'DTS-HD Master Audio Bumpers',
                'DTS-X Bumpers',
                'Other',
                'THX Bumpers'
            )),
            ('Cinema Spots', (
                '3D',
                'Coming Attractions',
                'Countdowns',
                'Courtesy',
                'Feature Presentation',
                'Intermissions',
                'Theater',
                'Trivia'

            )),
            ('Ratings Bumpers', (
                'MPAA',
                'BBFC',
                'DEJUS',
                'FSK'
            )),
        ))
    )

    def __init__(self, content_dir=None):
        self.trivia = []
        self.ratingsBumpers = {}
        self.audioFormatBumpers = {}
        self.cinemaSpots = {}
        self.music = []
        self.musicHandler = MusicHandler()
        self.triviaDirectoryHandler = TriviaDirectoryHandler()
        self.setContentDirectoryPath(content_dir)
        self.setupContentDirectory()
        self.loadContent()

    def setContentDirectoryPath(self, content_dir):
        self._contentDirectory = content_dir

    def _addDirectory(self, current, tree):
        if not util.vfs.exists(current):
            util.DEBUG_LOG('Creating: {0}'.format(repr(current)))
            util.vfs.makedirs(current)

        for branch in tree:
            if isinstance(branch, tuple):
                new = util.pathJoin(current, branch[0])
                self._addDirectory(new, branch[1])
            else:
                sub = util.pathJoin(current, branch)
                if util.vfs.exists(sub):
                    continue
                util.DEBUG_LOG('Creating: {0}'.format(repr(sub)))
                util.vfs.makedirs(sub)

    def setupContentDirectory(self):
        if not self._contentDirectory:  # or util.vfs.exists(self._contentDirectory):
            return
        self._addDirectory(self._contentDirectory, self._tree)

    def loadContent(self):
        self.loadMusic()
        self.loadTrivia()
        self.loadAudioFormatBumpers()
        self.loadCinemaSpots()
        self.loadRatingsBumpers()

    def loadMusic(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING MUSIC -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Music')
        paths = util.vfs.listdir(basePath)

        for path in paths:
            songs = self.musicHandler(path)
            if songs:
                self.music += songs

    def loadTrivia(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING TRIVIA -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Trivia')
        paths = util.vfs.listdir(basePath)

        for sub in paths:
            path = os.path.join(basePath, sub)
            if util.isDir(path):
                fmt = 'DIR'
            elif path.lower().endswith('.zip'):
                fmt = 'ZIP'
            else:
                fmt = 'FILE'

            util.DEBUG_LOG('Processing trivia ({0}): {1}'.format(fmt, os.path.basename(path)))
            if fmt == 'FILE':
                ts = self.triviaDirectoryHandler.getSlide(basePath, sub)
                if ts:
                    self.trivia.append(ts)
            elif fmt == 'DIR' or fmt == 'ZIP':
                items = self.triviaDirectoryHandler(path)
                if items:
                    self.trivia += items

    def loadAudioFormatBumpers(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING AUDIO FORMAT BUMPERS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Audio Format Bumpers')

        for bumpers in self.createBumpers(basePath, AudioFormat):
            self.audioFormatBumpers[bumpers.format] = bumpers

    def loadCinemaSpots(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING CINEMA SPOTS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Cinema Spots')

        for spots in self.createBumpers(basePath, CinemaSpot):
            self.cinemaSpots[spots.type] = spots

    def loadRatingsBumpers(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING RATINGS BUMPERS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Ratings Bumpers')

        for bumpers in self.createBumpers(basePath, Ratings):
            self.audioFormatBumpers[bumpers.system] = bumpers

    def createBumpers(self, basePath, bumpers_class):
        paths = util.vfs.listdir(basePath)

        for sub in paths:
            path = util.pathJoin(basePath, sub)
            if not util.isDir(path):
                continue

            name = sub.replace(' Bumpers', '')
            bumpers = bumpers_class(name)
            util.DEBUG_LOG('Loading: {0}'.format(bumpers))
            for v in path:
                vpath = os.path.join(path, v)
                bumpers.add(vpath)
            yield bumpers


class MusicHandler:
    _extensions = ('.mp3', '.wav')

    def __call__(self, path):
        p, ext = os.path.splitext(path)
        if ext.lower() in self._extensions:
            s = Song()
            s.name = os.path.basename(p)
            s.path = path
            util.DEBUG_LOG('Loading: {0}'.format(s))
            return [s]
        return None


class TriviaDirectoryHandler:
    _formatXML = 'slides.xml'
    _ratingNA = ('slide', 'rating')
    _questionNA = ('question', 'format')
    _clueNA = ('clue', 'format')
    _answerNA = ('answer', 'format')

    _imageExtensions = ('.jpg', '.png')

    def __call__(self, path):
        slideXML = util.pathJoin(path, self._formatXML)
        if not util.vfs.exists(slideXML):
            return self.processSimpleDir(path)

        f = util.vfs.File(slideXML, 'r')
        xml = f.read()
        f.close()
        slides = ET.fromstring(xml)
        slide = slides.find('slide')
        if slide is None:
            util.LOG('BAD_SLIDE_FILE')
            return None

        rating = self.getNodeAttribute(slide, self._ratingNA[0], self._ratingNA[1]) or ''
        questionRE = (self.getNodeAttribute(slide, self._questionNA[0], self._questionNA[1]) or '').replace('N/A', '')
        clueRE = self.getNodeAttribute(slide, self._clueNA[0], self._clueNA[1]) or ''.replace('N/A', '')
        answerRE = self.getNodeAttribute(slide, self._answerNA[0], self._answerNA[1]) or ''.replace('N/A', '')

        contents = util.vfs.listdir(path)

        questions = questionRE and [c for c in contents if re.search(questionRE, c)] or []
        clues = clueRE and [c for c in contents if re.search(clueRE, c)] or []
        answers = answerRE and [c for c in contents if re.search(answerRE, c)] or []

        items = {}

        for q in questions:
            name = q.split('_', 1)[0]
            ts = TriviaQA(util.pathJoin(path, q))
            ts.rating = rating
            ts.name = name
            items[name] = ts
            util.DEBUG_LOG('Loading: {0}'.format(ts))

        for a in answers:
            name = a.split('_', 1)[0]
            ts = items.get(name)
            if not ts:
                continue
            ts.answerPath = util.pathJoin(path, a)

        for c in clues:
            name = c.split('_', 1)[0]
            ts = items.get(name)
            if not ts:
                continue
            ts.addCluePath(util.pathJoin(path, c))

        return items.values()

    def processSimpleDir(self, path):
        contents = util.vfs.listdir(path)
        slides = []
        for c in contents:
            ts = self.getSlide(path, c)
            if not ts:
                continue
            slides.append(ts)

        return slides

    def getSlide(self, path, c):
        name, ext = os.path.splitext(c)
        if ext not in self._imageExtensions:
            return None

        ts = Trivia(util.pathJoin(path, c))
        ts.name = name
        util.DEBUG_LOG('Loading: {0}'.format(ts))
        return ts

    def getNodeAttribute(self, node, sub_node_name, attr_name):
        subNode = node.find(sub_node_name)
        if subNode is not None:
            return subNode.attrib.get(attr_name)
        return None
