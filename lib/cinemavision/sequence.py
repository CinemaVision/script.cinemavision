from xml.etree import ElementTree as ET
import xml.dom.minidom as minidom
import os

import util

LIMIT_FILE = 0
LIMIT_DIR = 1
LIMIT_DB_CHOICE = 2
LIMIT_BOOL = 3
LIMIT_BOOL_DEFAULT = 4


SETTINGS_DISPLAY = {
    '3D.intro': '3D Intro',
    '3D.outro': '3D Outro',
    'countdown': 'Countdown',
    'courtesy': 'Courtesy',
    'feature.intro': 'Feature Intro',
    'feature.outro': 'Feature Outro',
    'intermission': 'Intermission',
    'short.film': 'Short Film',
    'theater.intro': 'Theater Intro',
    'theater.outro': 'Theater Outro',
    'trailers.intro': 'Trailers Intro',
    'trailers.outro': 'Trailers Outro',
    'trivia.intro': 'Trivia Intro',
    'trivia.outro': 'Trivia Outro',
    'back': 'Back',
    'skip': 'Skip',
    'feature.queue=full': 'Feature queue is full',
    'feature.queue=empty': 'Feature queue is empty',
    'itunes': 'Apple iTunes',
    'kodidb': 'Kodi Database',
    'dir': 'Directory',
    'file': 'Single File',
    'content': 'Content',
    'standard': 'Standard',
    'af.detect': 'Auto-detect from source',
    'af.format': 'Choose format',
    'af.file': 'Choose file',
    'True': 'Yes',
    'False': 'No',
    'off': 'Off',
    'none': 'None',
    'fade': 'Fade',
    'slideL': 'Slide Left',
    'slideR': 'Slide Right',
    'slideU': 'Slide Up',
    'slideD': 'Slide Down',
    'video': 'Video',
    'image': 'Image',
    'slide': 'Slide'
}


def settingDisplay(setting):
    if setting is None or setting is 0:
        return ''

    try:
        return SETTINGS_DISPLAY.get(str(setting), setting)
    except:
        pass

    return setting


def strToBool(val):
    return bool(val == 'True')


def strToBoolWithDefault(val):
    if val is None:
        return None
    return bool(val == 'True')


################################################################################
# BASE class for all content items
################################################################################
class Item:
    _tag = 'item'   # XML tag when serialized
    _type = 'BASE'  # Name of the type of content. Equal to the xml tag type attribute when serialized
    _elements = ()  # Tuple of attributes to serialize
    displayName = ''
    typeChar = ''

    def __init__(self):
        self.enabled = True
        self.name = ''

    def _set(self, attr, value):
        conv = self.elementData('type')
        if conv:
            value = conv(value)
        setattr(self, attr, value)

    def copy(self):
        new = self.__class__()
        new.enabled = self.enabled
        new.name = self.name
        for e in self._elements:
            setattr(new, e['attr'], getattr(self, e['attr']))
        return new

    @property
    def fileChar(self):
        return self.typeChar

    def toNode(self):
        item = ET.Element(self._tag)
        item.set('type', self._type)
        item.set('enabled', str(self.enabled))
        if self.name:
            item.set('name', self.name)

        for e in self._elements:
            sub = ET.Element(e['attr'])
            val = getattr(self, e['attr'])
            if not val and val is not False:
                continue
            sub.text = unicode(val)
            item.append(sub)
        return item

    @staticmethod
    def fromNode(node):
        itype = node.attrib.get('type')
        if itype in CONTENT_CLASSES:
            return CONTENT_CLASSES[itype]._fromNode(node)

    @classmethod
    def _fromNode(cls, node):
        new = cls()
        new.enabled = node.attrib.get('enabled') == 'True'
        new.name = node.attrib.get('name') or ''
        for e in new._elements:
            sub = node.find(e['attr'])
            if sub is not None:
                if e['type']:
                    new._set(e['attr'], e['type'](sub.text))
                else:
                    new._set(e['attr'], sub.text)
        return new

    def elementData(self, element_name):
        for e in self._elements:
            if element_name == e['attr']:
                return e

    def getSettingOptions(self, attr):
        limits = self.elementData(attr)['limits']
        if isinstance(limits, list):
            limits = [(x, settingDisplay(x)) for x in limits]
        return limits

    def setSetting(self, setting, value):
        setattr(self, setting, value)

    def getSetting(self, attr):
        return getattr(self, attr)

    def getLive(self, attr):
        val = self.getSetting(attr)
        if val is None or val is 0:
            return util.getSettingDefault('{0}.{1}'.format(self._type, attr))
        return val

    def globalDefault(self, attr):
        return util.getSettingDefault('{0}.{1}'.format(self._type, attr))

    def getSettingIndex(self, attr):
        for i, e in enumerate(self._elements):
            if e['attr'] == attr:
                return i

    def getElement(self, attr):
        return self._elements[self.getSettingIndex(attr)]

    def getLimits(self, attr):
        return self._elements[self.getSettingIndex(attr)]['limits']

    def getType(self, attr):
        return self._elements[self.getSettingIndex(attr)]['type']

    def display(self):
        return self.name or self.displayName

    def getSettingDisplay(self, setting):
        val = getattr(self, setting)
        limits = self.getLimits(setting)
        if limits == LIMIT_BOOL_DEFAULT:
            if val is None:
                return 'Default ({0})'.format(settingDisplay(util.getSettingDefault('{0}.{1}'.format(self._type, setting))))
            return val is True and 'Yes' or 'No'

        if val is None or val is 0:
            return 'Default ({0})'.format(settingDisplay(util.getSettingDefault('{0}.{1}'.format(self._type, setting))))

        return unicode(settingDisplay(val))

    def DBChoices(self, attr):
        return None

    def elementVisible(self, e):
        return True


################################################################################
# FEATURE PRESENTATION
################################################################################
class Feature(Item):
    _type = 'feature'
    _elements = (
        {
            'attr': 'count',
            'type': int,
            'limits': (0, 10, 1),
            'name': 'Count',
            'default': 0
        },
        {
            'attr': 'ratingBumper',
            'type': None,
            'limits': [None, 'none', 'video', 'image'],
            'name': 'Rating Bumper',
            'default': None
        },
    )
    displayName = 'Feature'
    typeChar = 'F'

    def __init__(self):
        Item.__init__(self)
        self.count = 0
        self.ratingBumper = None

    def display(self):
        name = self.name or self.displayName
        if self.count > 1:
            return '{0} x {1}'.format(name, self.count)
        return name


################################################################################
# TRIVIA
################################################################################
class Trivia(Item):
    _type = 'trivia'
    _elements = (
        {
            'attr': 'format',
            'type': None,
            'limits': [None, 'slide', 'video'],
            'name': 'Format',
            'default': None
        },
        {'attr': 'duration',    'type': int, 'limits': (0, 60, 1), 'name': 'Duration (minutes)',          'default': 0},
        {'attr': 'qDuration',   'type': int, 'limits': (0, 60, 1), 'name': 'Question Duration (seconds)', 'default': 0},
        {'attr': 'cDuration',   'type': int, 'limits': (0, 60, 1), 'name': 'Clue Duration (seconds)',     'default': 0},
        {'attr': 'aDuration',   'type': int, 'limits': (0, 60, 1), 'name': 'Answer Duration (seconds)',   'default': 0},
        {'attr': 'sDuration',   'type': int, 'limits': (0, 60, 1), 'name': 'Single Duration (seconds)',   'default': 0},
        {
            'attr': 'transition',
            'type': None,
            'limits': [None, 'none', 'fade', 'slideL', 'slideR', 'slideU', 'slideD'],
            'name': 'Transition',
            'default': None
        },
        {
            'attr': 'transitionDuration',
            'type': int,
            'limits': (0, 2000, 100),
            'name': 'Transition Duration',
            'default': 0
        },
        {
            'attr': 'music',
            'type': None,
            'limits': [None, 'off', 'content', 'dir', 'file'],
            'name': 'Music',
            'default': None
        },
        {
            'attr': 'musicDir',
            'type': None,
            'limits': LIMIT_DIR,
            'name': 'Path',
            'default': ''
        },
        {
            'attr': 'musicFile',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'File',
            'default': ''
        }
    )
    displayName = 'Trivia Slides'
    typeChar = 'Q'

    def __init__(self):
        Item.__init__(self)
        self.format = None
        self.duration = 0
        self.qDuration = 0
        self.cDuration = 0
        self.aDuration = 0
        self.sDuration = 0
        self.transition = None
        self.transitionDuration = 0
        self.music = None
        self.musicDir = None
        self.musicFile = None

    def display(self):
        name = self.name or self.displayName
        if self.duration > 0:
            return '{0} ({1}m)'.format(name, self.duration)
        return name

    def getLive(self, attr):
        if not attr == 'musicDir' or self.music is not None:
            return Item.getLive(self, attr)

        return util.getSettingDefault('{0}.{1}'.format(self._type, attr))

    def elementVisible(self, e):
        attr = e['attr']
        if attr != 'format' and self.getLive('format') == 'video':
            return False

        if attr == 'musicDir':
            if self.getLive('music') != 'dir':
                return False
        elif attr == 'musicFile':
            if self.getLive('music') != 'file':
                return False
        elif attr == 'transitionDuration':
            transition = self.getLive('transition')
            if not transition or transition == 'none':
                return False

        return True


################################################################################
# Trailer
################################################################################
class Trailer(Item):
    _type = 'trailer'
    _elements = (
        {
            'attr': 'source',
            'type': None,
            'limits': [None, 'itunes', 'kodidb', 'dir', 'file'],
            'name': 'Source',
            'default': None
        },
        {
            'attr': 'count',
            'type': int,
            'limits': (0, 10, 1),
            'name': 'Count',
            'default': 0
        },
        {
            'attr': 'limitRating',
            'type': strToBoolWithDefault,
            'limits': LIMIT_BOOL_DEFAULT,
            'name': 'Limit By Rating',
            'default': None
        },
        {
            'attr': 'limitGenre',
            'type': strToBoolWithDefault,
            'limits': LIMIT_BOOL_DEFAULT,
            'name': 'Limit By Genre',
            'default': None
        },
        {
            'attr': 'quality',
            'type': None,
            'limits': [None, '480p', '720p', '1080p'],
            'name': 'Quality',
            'default': None
        },
        {
            'attr': 'file',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'Path',
            'default': ''
        },
        {
            'attr': 'dir',
            'type': None,
            'limits': LIMIT_DIR,
            'name': 'Path',
            'default': ''
        }
    )
    displayName = 'Trailer'
    typeChar = 'T'

    def __init__(self):
        Item.__init__(self)
        self.count = 0
        self.source = None
        self.file = None
        self.dir = None
        self.limitRating = None
        self.limitGenre = None
        self.quality = None

    def display(self):
        name = self.name or self.displayName
        if self.count > 1:
            return '{0} x {1}'.format(name, self.count)
        return name

    def elementVisible(self, e):
        attr = e['attr']
        if attr == 'file':
            if self.getLive('source') != 'file':
                return False
        elif attr == 'dir':
            if self.getLive('source') != 'dir':
                return False
        elif attr == 'count':
            if self.getLive('source') not in ('dir', 'itunes', 'kodidb'):
                return False
        elif attr in ('limitRating', 'limitGenre'):
            if self.getLive('source') not in ('itunes', 'kodidb'):
                return False
        elif attr == 'quality':
            if self.getLive('source') != 'itunes':
                return False
        return True


################################################################################
# VIDEO
################################################################################
class Video(Item):
    _type = 'video'
    _elements = (
        {
            'attr': 'vtype',
            'type': None,
            'limits': [
                '3D.intro',
                '3D.outro',
                'countdown',
                'courtesy',
                'feature.intro',
                'feature.outro',
                'intermission',
                'short.film',
                'theater.intro',
                'theater.outro',
                'trailers.intro',
                'trailers.outro',
                'trivia.intro',
                'trivia.outro',
                'file'
            ],
            'name': 'Type'
        },
        {
            'attr': 'random',
            'type': strToBool,
            'limits': LIMIT_BOOL,
            'name': 'Random'
        },
        {
            'attr': 'source',
            'type': None,
            'limits': LIMIT_DB_CHOICE,
            'name': 'Source'
        },
        {
            'attr': 'file',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'File'
        },
        {
            'attr': 'play3D',
            'type': strToBool,
            'limits': LIMIT_BOOL,
            'name': 'Play 3D If 3D Feature'
        }
    )
    displayName = 'Video Bumper'
    typeChar = 'V'

    def __init__(self):
        Item.__init__(self)
        self.vtype = ''
        self.random = True
        self.source = ''
        self.file = ''
        self.play3D = True

    def elementVisible(self, e):
        attr = e['attr']
        if attr == 'source':
            return self.vtype != 'file' and not self.random
        elif attr == 'file':
            return self.vtype == 'file'
        elif attr == 'random':
            return self.vtype != 'file'
        elif attr == 'play3D':
            return self.random and self.vtype not in ('3D.intro', '3D.outro', 'file')

        return True

    def display(self):
        if self.name:
            return self.name

        if not self.vtype:
            return self.displayName

        return settingDisplay(self.vtype)

    def DBChoices(self, attr):
        import database as DB
        return [(x.path, os.path.basename(x.path)) for x in DB.VideoBumpers.select().where(DB.VideoBumpers.type == self.vtype)]


################################################################################
# AUDIOFORMAT
################################################################################
class AudioFormat(Item):
    _type = 'audioformat'
    _elements = (
        {
            'attr': 'method',
            'type': None,
            'limits': [None, 'af.detect', 'af.format', 'af.file'],
            'name': 'Method',
            'default': None
        },
        {
            'attr': 'fallback',
            'type': None,
            'limits': [None, 'af.format', 'af.file'],
            'name': 'Fallback',
            'default': None
        },
        {
            'attr': 'file',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'Path',
            'default': ''
        },
        {
            'attr': 'format',
            'type': None,
            'limits': [
                None, 'Auro-3D', 'Dolby TrueHD', 'DTS-X', 'DTS-HD Master Audio', 'DTS', 'Dolby Atmos', 'THX', 'Dolby Digital Plus', 'Dolby Digital', 'Other'
            ],
            'name': 'Format',
            'default': None
        },
        {
            'attr': 'play3D',
            'type': strToBool,
            'limits': LIMIT_BOOL,
            'name': 'Play 3D If 3D Feature'
        }
    )
    displayName = 'Audio Format Bumper'
    typeChar = 'A'

    def __init__(self):
        Item.__init__(self)
        self.method = None
        self.fallback = None
        self.format = None
        self.file = None
        self.play3D = True

    def elementVisible(self, e):
        attr = e['attr']
        if attr == 'fallback':
            return self.getLive('method') == 'af.detect'
        elif attr == 'file':
            return self.getLive('method') == 'af.file' or (self.getLive('method') == 'af.detect' and self.getLive('fallback') == 'af.file')
        elif attr == 'format':
            return self.getLive('method') == 'af.format' or (self.getLive('method') == 'af.detect' and self.getLive('fallback') == 'af.format')
        elif attr == 'play3D':
            return self.getLive('method') in (None, 'af.detect', 'af.format')

        return True


################################################################################
# ACTION
################################################################################
class Action(Item):
    _type = 'action'
    displayName = 'Action'
    typeChar = '!'
    fileChar = '_'


################################################################################
# COMMAND
################################################################################
class Command(Item):
    _type = 'command'
    _elements = (
        {
            'attr': 'command',
            'type': None,
            'limits': ['back', 'skip'],
            'name': 'Command'
        },
        {
            'attr': 'arg',
            'type': None,
            'limits': None,
            'name': 'Argument'
        },
        {
            'attr': 'condition',
            'type': None,
            'limits': ['feature.queue=full', 'feature.queue=empty', 'none'],
            'name': 'Condition'
        }
    )
    displayName = 'Command'
    typeChar = 'C'

    def _set(self, attr, value):
        if self.command in ('back', 'skip'):
            if attr == 'arg':
                value = int(value)
        Item._set(self, attr, value)

    def __init__(self):
        Item.__init__(self)
        self.command = ''
        self.arg = ''
        self.condition = ''

    def getLimits(self, attr):
        e = self.getElement(attr)
        if not e['attr'] == 'arg' or self.command not in ('skip', 'back'):
            return Item.getLimits(self, attr)

        return (1, 99, 1)

    def getType(self, attr):
        e = self.getElement(attr)
        if not e['attr'] == 'arg' or self.command not in ('skip', 'back'):
            return Item.getType(self, attr)

        return int

    def getSettingOptions(self, setting):
        if setting == 'arg':
            if self.command in ('back', 'skip'):
                return (1, 99, 1)
        else:
            return Item.getSettingOptions(self, setting)

    def setSetting(self, setting, value):
        Item.setSetting(self, setting, value)

        if setting == 'command':
            if self.command == 'back':
                if not self.condition:
                    self.condition = 'feature.queue=full'
                if not self.arg:
                    self.arg = 2
            elif self.command == 'skip':
                if not self.condition:
                    self.condition = 'feature.queue=empty'
                if not self.arg:
                    self.arg = 2
            else:
                self.condition = ''

    def getSetting(self, setting):
        if self.command in ('back', 'skip'):
            if setting == 'arg':
                if not self.arg:
                    self.arg = 2
        return Item.getSetting(self, setting)

    def display(self):
        name = self.name or self.displayName
        command = self.command and ' ({0}:{1})'.format(self.command, self.arg) or ''
        return '{0}{1}'.format(name, command)


CONTENT_CLASSES = {
    'action':       Action,
    'audioformat':  AudioFormat,
    'command':      Command,
    'feature':      Feature,
    'trivia':       Trivia,
    'trailer':      Trailer,
    'video':        Video
}

ITEM_TYPES = [
    ('!', 'Action', '_', Action),
    ('A', 'Audio Format Bumper', 'A', AudioFormat),
    ('C', 'Command', 'C', Command),
    ('F', 'Feature', 'F', Feature),
    ('Q', 'Trivia Slides', 'Q', Trivia),
    ('T', 'Trailer', 'T', Trailer),
    ('V', 'Video Bumper', 'V', Video),
]


def getItem(token):
    for i in ITEM_TYPES:
        if i[0] == token:
            return i[3]


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem)
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml().encode('ascii', 'xmlcharrefreplace')


def getSaveString(items):
    base = ET.Element('sequence')
    for item in items:
        base.append(item.toNode())

    return prettify(base)


def getItemsFromString(xml_string):
    e = ET.fromstring(xml_string)
    items = []
    for node in e.findall('item'):
        items.append(Item.fromNode(node))
    return items


def loadSequence(path):
    import xbmcvfs
    f = xbmcvfs.File(path, 'r')
    xmlString = f.read().decode('utf-8')
    f.close()
    return getItemsFromString(xmlString)
