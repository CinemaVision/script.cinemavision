import util

import os
import re
from xml.etree import ElementTree as ET
from peewee import peewee

DB = peewee.SqliteDatabase(util.pathJoin(util.STORAGE_PATH, 'content.db'))

util.DEBUG_LOG('Creating database...')


class ContentBase(peewee.Model):
    name = peewee.CharField()
    accessed = peewee.IntegerField(default=0)
    pack = peewee.TextField(null=True)

    class Meta:
        database = DB

util.DEBUG_LOG(' - Music')


class Song(ContentBase):
    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    path = peewee.CharField(unique=True)

Song.create_table(fail_silently=True)

util.DEBUG_LOG(' - Tivia')


class Trivia(ContentBase):
    type = peewee.CharField()

    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    questionPath = peewee.CharField(unique=True, null=True)
    cluePath1 = peewee.CharField(unique=True, null=True)
    cluePath2 = peewee.CharField(unique=True, null=True)
    cluePath3 = peewee.CharField(unique=True, null=True)
    answerPath = peewee.CharField(unique=True, null=True)

Trivia.create_table(fail_silently=True)

util.DEBUG_LOG(' - AudioFormatBumpers')


class AudioFormatBumpers(ContentBase):
    is3D = peewee.BooleanField(default=False)
    format = peewee.CharField()
    path = peewee.CharField(unique=True)

AudioFormatBumpers.create_table(fail_silently=True)

util.DEBUG_LOG(' - RatingsBumpers')


class RatingsBumpers(ContentBase):
    is3D = peewee.BooleanField(default=False)
    system = peewee.CharField(default='MPAA')
    path = peewee.CharField(unique=True)

RatingsBumpers.create_table(fail_silently=True)

util.DEBUG_LOG(' - CinemaSpots')


class CinemaSpots(ContentBase):
    type = peewee.CharField()
    is3D = peewee.BooleanField()

    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    path = peewee.CharField(unique=True)

CinemaSpots.create_table(fail_silently=True)

util.DEBUG_LOG('Database created')


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
            self.musicHandler(basePath, path)

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
                self.triviaDirectoryHandler.getSlide(basePath, sub)
            elif fmt == 'DIR' or fmt == 'ZIP':
                self.triviaDirectoryHandler(path)

    def loadAudioFormatBumpers(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING AUDIO FORMAT BUMPERS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Audio Format Bumpers')

        self.createBumpers(basePath, AudioFormatBumpers, 'format')

    def loadCinemaSpots(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING CINEMA SPOTS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Cinema Spots')

        self.createBumpers(basePath, CinemaSpots, 'type')

    def loadRatingsBumpers(self):
        util.DEBUG_LOG('')
        util.DEBUG_LOG('[- LOADING RATINGS BUMPERS -]')
        util.DEBUG_LOG('')

        basePath = util.pathJoin(self._contentDirectory, 'Videos', 'Ratings Bumpers')

        self.createBumpers(basePath, RatingsBumpers, 'system')

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
                util.DEBUG_LOG('Loading {0}: [ {1} ]'.format(model.__name__, name))
                model.get_or_create(
                    path=os.path.join(path, v),
                    defaults={
                        type_name: type_,
                        'name': name,
                        'is3D': '3D' in v
                    }
                )


class MusicHandler:
    _extensions = ('.mp3', '.wav')

    def __call__(self, base, path):
        p, ext = os.path.splitext(path)
        if ext.lower() in self._extensions:
            path = util.pathJoin(base, path)
            name = os.path.basename(p)
            util.DEBUG_LOG('Loading Song: [ {0} ]'.format(name))
            Song.get_or_create(
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

    def __call__(self, basePath):
        slideXML = util.pathJoin(basePath, self._formatXML)
        if not util.vfs.exists(slideXML):
            return self.processSimpleDir(basePath)

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

            util.DEBUG_LOG('Loading Trivia(QA): [ {0} ]'.format(name))

            defaults = {
                    'type': 'QA',
                    'name': name,
                    'rating': rating,
                    'questionPath': questionPath
            }

            ct = 1
            for c in data['c']:
                defaults['cluePath{0}'.format(ct)] = c
                ct += 1

            Trivia.get_or_create(
                answerPath=answerPath,
                defaults=defaults
            )

    def processSimpleDir(self, path):
        contents = util.vfs.listdir(path)
        for c in contents:
            self.getSlide(path, c)

    def getSlide(self, path, c):
        name, ext = os.path.splitext(c)
        if ext not in self._imageExtensions:
            return

        util.DEBUG_LOG('Loading Trivia (fact): [ {0} ]'.format(name))
        Trivia.get_or_create(
                answerPath=util.pathJoin(path, c),
                defaults={
                    'type': 'fact',
                    'name': name
                }
            )

    def getNodeAttribute(self, node, sub_node_name, attr_name):
        subNode = node.find(sub_node_name)
        if subNode is not None:
            return subNode.attrib.get(attr_name)
        return None
