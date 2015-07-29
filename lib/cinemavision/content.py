import os
import re
from xml.etree import ElementTree as ET

import util

TYPE_IDS = {
    '3D Intro':       '3D.intro',
    '3D Outro':       '3D.outro',
    'Countdown':      'countdown',
    'Courtesy':       'courtesy',
    'Feature Intro':  'feature.intro',
    'Feature Outro':  'feature.outro',
    'Intermission':   'intermission',
    'Short Film':     'short.film',
    'Theater Intro':  'theater.intro',
    'Theater Outro':  'theater.outro',
    'Trailers Intro': 'trailers.intro',
    'Trailers Outro': 'trailers.outro',
    'Trivia Intro':   'trivia.intro',
    'Trivia Outro':   'trivia.outro'
}


class UserContent:
    _tree = (
        ('Audio Format Bumpers', (
            'Auro-3D',
            'Dolby Atmos',
            'Dolby Digital',
            'Dolby Digital Plus',
            'Dolby TrueHD',
            'DTS',
            'DTS-HD Master Audio',
            'DTS-X',
            'Other',
            'THX'
        )),
        'Music',
        ('Ratings Bumpers', (
            'MPAA',
            'BBFC',
            'DEJUS',
            'FSK'
        )),
        'Trailers',
        'Trivia Slides',
        ('Video Bumpers', (
            '3D Intro',
            '3D Outro',
            'Countdown',
            'Courtesy',
            'Feature Intro',
            'Feature Outro',
            'Intermission',
            'Short Film',
            'Theater Intro',
            'Theater Outro',
            'Trailers Intro',
            'Trailers Outro',
            'Trivia Intro',
            'Trivia Outro'
        ))
    )

    def __init__(self, content_dir=None, callback=None):
        self._callback = callback
        self.setupDB()
        self.musicHandler = MusicHandler(self.db, self.log)
        self.triviaDirectoryHandler = TriviaDirectoryHandler(self.db, self.log)
        self.setContentDirectoryPath(content_dir)
        self.setupContentDirectory()
        self.loadContent()

    def setupDB(self):
        try:
            util.CALLBACK = self._callback
            import database
            self.db = database
        finally:
            util.CALLBACK = None

    def log(self, msg):
        util.DEBUG_LOG(msg)

        if not self._callback:
            return

        self._callback(msg)

    def logHeading(self, heading):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- {0} -]'.format(heading))
        util.DEBUG_LOG('')

        if not self._callback:
            return

        self._callback(None, heading)

    def setContentDirectoryPath(self, content_dir):
        self._contentDirectory = content_dir

    def _addDirectory(self, current, tree):
        if not util.vfs.exists(current):
            util.DEBUG_LOG('Creating: {0}'.format(repr(current)))
            util.vfs.mkdirs(current)

        for branch in tree:
            if isinstance(branch, tuple):
                new = util.pathJoin(current, branch[0])
                self._addDirectory(new, branch[1])
            else:
                sub = util.pathJoin(current, branch)
                if util.vfs.exists(sub):
                    continue
                util.DEBUG_LOG('Creating: {0}'.format(repr(sub)))
                util.vfs.mkdirs(sub)

    def setupContentDirectory(self):
        if not self._contentDirectory:  # or util.vfs.exists(self._contentDirectory):
            return
        self._addDirectory(self._contentDirectory, self._tree)

    def loadContent(self):
        self.loadMusic()
        self.loadTrivia()
        self.loadAudioFormatBumpers()
        self.loadVideoBumpers()
        self.loadRatingsBumpers()

    def loadMusic(self):
        self.logHeading('LOADING MUSIC')

        basePath = util.pathJoin(self._contentDirectory, 'Music')
        paths = util.vfs.listdir(basePath)

        for path in paths:
            self.musicHandler(basePath, path)

    def loadTrivia(self):
        self.logHeading('LOADING TRIVIA')

        basePath = util.pathJoin(self._contentDirectory, 'Trivia Slides')
        paths = util.vfs.listdir(basePath)

        for sub in paths:
            path = os.path.join(basePath, sub)
            if util.isDir(path):
                fmt = 'DIR'
            elif path.lower().endswith('.zip'):
                fmt = 'ZIP'
            else:
                fmt = 'FILE'

            self.log('Processing trivia ({0}): {1}'.format(fmt, os.path.basename(path)))

            if fmt == 'FILE':
                self.triviaDirectoryHandler.getSlide(basePath, sub)
            elif fmt == 'DIR' or fmt == 'ZIP':
                self.triviaDirectoryHandler(path)

    def loadAudioFormatBumpers(self):
        self.logHeading('LOADING AUDIO FORMAT BUMPERS')

        basePath = util.pathJoin(self._contentDirectory, 'Audio Format Bumpers')

        self.createBumpers(basePath, self.db.AudioFormatBumpers, 'format')

    def loadVideoBumpers(self):
        self.logHeading('LOADING VIDEO BUMPERS')

        basePath = util.pathJoin(self._contentDirectory, 'Video Bumpers')

        self.createBumpers(basePath, self.db.VideoBumpers, 'type')

    def loadRatingsBumpers(self):
        self.logHeading('LOADING RATINGS BUMPERS')

        basePath = util.pathJoin(self._contentDirectory, 'Ratings Bumpers')

        self.createBumpers(basePath, self.db.RatingsBumpers, 'system')

    def createBumpers(self, basePath, model, type_name):
        paths = util.vfs.listdir(basePath)

        for sub in paths:
            path = util.pathJoin(basePath, sub)
            if not util.isDir(path):
                continue

            type_ = sub.replace(' Bumpers', '')
            for v in util.vfs.listdir(path):
                name, ext = os.path.splitext(v)
                if ext not in ('.mp4'):
                    continue
                self.log('Loading {0}: [ {1} ]'.format(model.__name__, name))
                model.get_or_create(
                    path=os.path.join(path, v),
                    defaults={
                        type_name: TYPE_IDS.get(type_, type_),
                        'name': name,
                        'is3D': '3D' in v
                    }
                )


class MusicHandler:
    _extensions = ('.mp3', '.wav')

    def __init__(self, db, callback=None):
        self.db = db
        self._callback = callback

    def __call__(self, base, path):
        p, ext = os.path.splitext(path)
        if ext.lower() in self._extensions:
            path = util.pathJoin(base, path)
            name = os.path.basename(p)
            self._callback('Loading Song: [ {0} ]'.format(name))
            self.db.Song.get_or_create(
                path=path,
                defaults={'name': name}
            )


class TriviaDirectoryHandler:
    _formatXML = 'slides.xml'
    _ratingNA = ('slide', 'rating')
    _questionNA = ('question', 'format')
    _clueNA = ('clue', 'format')
    _answerNA = ('answer', 'format')

    _imageExtensions = ('.jpg', '.png')

    def __init__(self, db, callback=None):
        self.db = db
        self._callback = callback

    def __call__(self, basePath):
        slideXML = util.pathJoin(basePath, self._formatXML)
        if not util.vfs.exists(slideXML):
            return self.processSimpleDir(basePath)

        f = util.vfs.File(slideXML, 'r')
        xml = f.read()
        f.close()
        xml = xml.replace('">', '" />')  # Clean broken slide tags
        slides = ET.fromstring(xml)
        slide = slides.find('slide')
        if slide is None:
            util.LOG('BAD_SLIDE_FILE')
            return None

        pack = os.path.basename(basePath.rstrip('\\/'))

        rating = self.getNodeAttribute(slide, self._ratingNA[0], self._ratingNA[1]) or ''
        questionRE = (self.getNodeAttribute(slide, self._questionNA[0], self._questionNA[1]) or '').replace('N/A', '')
        clueRE = self.getNodeAttribute(slide, self._clueNA[0], self._clueNA[1]) or ''.replace('N/A', '')
        answerRE = self.getNodeAttribute(slide, self._answerNA[0], self._answerNA[1]) or ''.replace('N/A', '')

        contents = util.vfs.listdir(basePath)

        trivia = {}

        for c in contents:
            path = util.pathJoin(basePath, c)
            name = c.split('_', 1)[0]

            if name not in trivia:
                trivia[name] = {'q': '', 'c': [], 'a': ''}

            if re.search(questionRE, c):
                trivia[name]['q'] = path
            elif re.search(answerRE, c):
                trivia[name]['a'] = path
            elif re.search(clueRE, c):
                trivia[name]['c'].append(path)

        for name, data in trivia.items():
            questionPath = data['q']
            answerPath = data['a']

            if not questionPath or not answerPath:
                continue

            self._callback('Loading Trivia(QA): [ {0} ]'.format(name))

            defaults = {
                    'type': 'QA',
                    'TID': '{0}.{1}'.format(pack, name),
                    'name': name,
                    'rating': rating,
                    'questionPath': questionPath
            }

            ct = 1
            for c in data['c']:
                defaults['cluePath{0}'.format(ct)] = c
                ct += 1

            self.db.Trivia.get_or_create(
                answerPath=answerPath,
                defaults=defaults
            )

    def processSimpleDir(self, path):
        pack = os.path.basename(path.rstrip('\\/'))
        contents = util.vfs.listdir(path)
        for c in contents:
            self.getSlide(path, c, pack)

    def getSlide(self, path, c, pack=''):
        name, ext = os.path.splitext(c)
        if ext not in self._imageExtensions:
            return

        self._callback('Loading Trivia (fact): [ {0} ]'.format(name))
        self.db.Trivia.get_or_create(
                answerPath=util.pathJoin(path, c),
                defaults={
                    'type': 'fact',
                    'TID': '{0}.{1}'.format(pack, name),
                    'name': name
                }
            )

    def getNodeAttribute(self, node, sub_node_name, attr_name):
        subNode = node.find(sub_node_name)
        if subNode is not None:
            return subNode.attrib.get(attr_name)
        return None
