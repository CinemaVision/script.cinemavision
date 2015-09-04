import os
import re
from xml.etree import ElementTree as ET

import util
import mutagen
import hachoir
import database as DB


mutagen.setFileOpener(util.vfs.File)

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


def getBumperDir(ID):
    for dirname, tid in TYPE_IDS.items():
        if tid == ID:
            break
    else:
        return None

    return ('Video Bumpers', dirname)


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
            'Datasat',
            'Other',
            'THX'
        )),
        'Music',
        'Actions',
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

    def __init__(self, content_dir=None, callback=None, db_path=None):
        self._callback = callback
        self.setupDB(db_path)
        self.musicHandler = MusicHandler(self.log)
        self.triviaDirectoryHandler = TriviaDirectoryHandler(self.log)
        self.setContentDirectoryPath(content_dir)
        if not db_path:
            self.setupContentDirectory()
        self.loadContent()

    def setupDB(self, db_path):
        try:
            util.CALLBACK = self._callback
            DB.initialize(db_path)
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

        total = float(len(paths))
        for ct, path in enumerate(paths):
            pct = int((ct/total)*20)
            self._callback(pct=pct)
            self.musicHandler(basePath, path)

    def loadTrivia(self):
        self.logHeading('LOADING TRIVIA')

        basePath = util.pathJoin(self._contentDirectory, 'Trivia Slides')
        paths = util.vfs.listdir(basePath)

        total = float(len(paths))
        for ct, sub in enumerate(paths):
            pct = 20 + int((ct/total)*20)
            self._callback(pct=pct)
            path = os.path.join(basePath, sub)
            if util.isDir(path):
                if sub.startswith('_Exclude'):
                    util.DEBUG_LOG('SKIPPING EXCLUDED DIR: {0}'.format(sub))
                    continue
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

        self.createBumpers(basePath, DB.AudioFormatBumpers, 'format', 40)

    def loadVideoBumpers(self):
        self.logHeading('LOADING VIDEO BUMPERS')

        basePath = util.pathJoin(self._contentDirectory, 'Video Bumpers')

        self.createBumpers(basePath, DB.VideoBumpers, 'type', 60)

    def loadRatingsBumpers(self):
        self.logHeading('LOADING RATINGS BUMPERS')

        basePath = util.pathJoin(self._contentDirectory, 'Ratings Bumpers')

        self.createBumpers(basePath, DB.RatingsBumpers, 'system', 80)

    def createBumpers(self, basePath, model, type_name, pct_start):
        paths = util.vfs.listdir(basePath)
        total = float(len(paths))

        for ct, sub in enumerate(paths):
            pct = pct_start + int((ct/total)*20)
            self._callback(pct=pct)

            path = util.pathJoin(basePath, sub)
            if not util.isDir(path):
                continue

            if sub.startswith('_Exclude'):
                util.DEBUG_LOG('SKIPPING EXCLUDED DIR: {0}'.format(sub))
                continue

            type_ = sub.replace(' Bumpers', '')
            for v in util.vfs.listdir(path):
                name, ext = os.path.splitext(v)
                isImage = False
                if ext in util.videoExtensions:
                    isImage = False
                elif ext in util.imageExtensions:
                    isImage = True
                else:
                    continue

                self.log('Loading {0} ({1}): [ {2} ]'.format(model.__name__, sub, name))
                model.get_or_create(
                    path=os.path.join(path, v),
                    defaults={
                        type_name: TYPE_IDS.get(type_, type_),
                        'name': name,
                        'is3D': '3D' in v,
                        'isImage': isImage
                    }
                )


class MusicHandler:
    def __init__(self, callback=None):
        self._callback = callback

    def __call__(self, base, path):
        p, ext = os.path.splitext(path)
        if ext.lower() in util.musicExtensions:
            path = util.pathJoin(base, path)
            name = os.path.basename(p)
            data = mutagen.File(path)

            try:
                DB.Song.get(DB.Song.path == path)
                self._callback('Loading Song (exists): [ {0} ]'.format(name))
            except DB.peewee.DoesNotExist:
                data = mutagen.File(path)
                if data:
                    duration = data.info.length
                    self._callback('Loading Song (new): [ {0} ({1}) ]'.format(name, data.info.pprint()))
                else:
                    duration = 0
                DB.Song.create(
                    path=path,
                    name=name,
                    duration=duration
                )


class TriviaDirectoryHandler:
    _formatXML = 'slides.xml'
    _ratingNA = ('slide', 'rating')
    _questionNA = ('question', 'format')
    _clueNA = ('clue', 'format')
    _answerNA = ('answer', 'format')

    _defaultQRegEx = '_q\.jpg|png|gif|bmp'
    _defaultCRegEx = '_c(\d)?\.jpg|png|gif|bmp'
    _defaultARegEx = '_a\.jpg|png|gif|bmp'

    def __init__(self, callback=None):
        self._callback = callback

    def __call__(self, basePath):
        hasSlidesXML = False
        slideXML = util.pathJoin(basePath, self._formatXML)
        if util.vfs.exists(slideXML):
            hasSlidesXML = True

        pack = os.path.basename(basePath.rstrip('\\/'))

        xml = None
        slide = None

        if hasSlidesXML:
            try:
                f = util.vfs.File(slideXML, 'r')
                xml = f.read()
            finally:
                f.close()

            try:
                slides = ET.fromstring(xml)
                slide = slides.find('slide')
            except ET.ParseError:
                util.DEBUG_LOG('bad slides.xml')
            except:
                util.ERROR()
                slide = None

        if slide:
            rating = self.getNodeAttribute(slide, self._ratingNA[0], self._ratingNA[1]) or ''
            questionRE = (self.getNodeAttribute(slide, self._questionNA[0], self._questionNA[1]) or '').replace('N/A', '')
            clueRE = self.getNodeAttribute(slide, self._clueNA[0], self._clueNA[1]) or ''.replace('N/A', '')
            answerRE = self.getNodeAttribute(slide, self._answerNA[0], self._answerNA[1]) or ''.replace('N/A', '')
        else:
            rating = ''
            questionRE = self._defaultQRegEx
            clueRE = self._defaultCRegEx
            answerRE = self._defaultARegEx

        contents = util.vfs.listdir(basePath)

        trivia = {}

        for c in contents:
            path = util.pathJoin(basePath, c)
            base, ext = os.path.splitext(c)

            if not ext.lower() in util.imageExtensions:
                if ext.lower() in util.videoExtensions:
                    self.getSlide(basePath, c, pack)
                continue

            ttype = ''
            clueCount = 0

            if re.search(questionRE, c):
                name = re.split(questionRE, c)[0]
                ttype = 'q'
            elif re.search(answerRE, c):
                name = re.split(answerRE, c)[0]
                ttype = 'a'
            elif re.search(clueRE, c):
                name = re.split(clueRE, c)[0]

                try:
                    clueCount = re.search(clueRE, c).group(1)
                except:
                    pass

                ttype = 'c'
            else:  # A still
                name = re.split(clueRE, c)[0]
                ttype = 'a'

            if name not in trivia:
                trivia[name] = {'q': None, 'c': {}, 'a': None}

            if ttype == 'q' or ttype == 'a':
                trivia[name][ttype] = path
            elif ttype == 'c':
                trivia[name]['c'][clueCount] = path

        for name, data in trivia.items():
            questionPath = data['q']
            answerPath = data['a']

            if not answerPath:
                continue

            if questionPath:
                self._callback('Loading Trivia(QA): [ {0} ]'.format(name))
            else:
                self._callback('Loading Trivia(Single): [ {0} ]'.format(name))

            defaults = {
                    'type': 'QA',
                    'TID': '{0}.{1}'.format(pack, name),
                    'name': name,
                    'rating': rating,
                    'questionPath': questionPath
            }

            for ct, key in enumerate(sorted(data['c'].keys())):
                defaults['cluePath{0}'.format(ct)] = data['c'][key]
            try:
                DB.Trivia.get_or_create(
                    answerPath=answerPath,
                    defaults=defaults
                )
            except:
                print data
                util.ERROR()
                raise

    def processSimpleDir(self, path):
        pack = os.path.basename(path.rstrip('\\/'))
        contents = util.vfs.listdir(path)
        for c in contents:
            self.getSlide(path, c, pack)

    def getSlide(self, path, c, pack=''):
        name, ext = os.path.splitext(c)
        duration = 0
        path = util.pathJoin(path, c)

        try:
            DB.Trivia.get(DB.Trivia.answerPath == path)
            self._callback('Loading Trivia (exists): [ {0} ]'.format(name))
        except DB.peewee.DoesNotExist:
            if ext.lower() in util.videoExtensions:
                ttype = 'video'
                parser = hachoir.hachoir_parser.createParser(path)
                metadata = hachoir.hachoir_metadata.extractMetadata(parser)
                durationDT = None
                if metadata:
                    durationDT = metadata.get('duration')
                    duration = durationDT and util.datetimeTotalSeconds(durationDT) or 0
                self._callback('Loading Trivia (video): [ {0} ({1}) ]'.format(name, durationDT))

            elif ext.lower() in util.imageExtensions:
                ttype = 'fact'
                self._callback('Loading Trivia (fact): [ {0} ]'.format(name))
            else:
                return

            DB.Trivia.get_or_create(
                    answerPath=path,
                    defaults={
                        'type': ttype,
                        'TID': '{0}.{1}'.format(pack, name),
                        'name': name,
                        'duration': duration
                    }
                )

    def getNodeAttribute(self, node, sub_node_name, attr_name):
        subNode = node.find(sub_node_name)
        if subNode is not None:
            return subNode.attrib.get(attr_name)
        return None
