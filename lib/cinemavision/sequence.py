from xml.etree import ElementTree as ET
import xml.dom.minidom as minidom

LIMIT_FILE = 0
LIMIT_BOOL = 1


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
    True: 'Yes',
    False: 'No'
}


def strToBool(val):
    return val == 'True'


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
            attr = getattr(self, e['attr'])
            if not attr:
                continue
            sub.text = str(attr)
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
                new._set(e['attr'], e['type'] and e['type'](sub.text) or sub.text)
        return new

    def elementData(self, element_name):
        for e in self._elements:
            if element_name == e['attr']:
                return e

    def getSettingOptions(self, setting):
        limits = self.elementData(setting)['limits']
        if isinstance(limits, list):
            limits = [(x, SETTINGS_DISPLAY.get(x, x)) for x in limits]
        return limits

    def setSetting(self, setting, value):
        setattr(self, setting, value)

    def getSetting(self, setting):
        return getattr(self, setting)

    def getSettingIndex(self, setting):
        for i, e in enumerate(self._elements):
            if e['attr'] == setting:
                return i

    def getLimits(self, idx):
        return self._elements[idx]['limits']

    def getType(self, idx):
        return self._elements[idx]['type']

    def display(self):
        return self.displayName

    def getSettingDisplay(self, setting):
        val = getattr(self, setting)
        if val in SETTINGS_DISPLAY:
            return SETTINGS_DISPLAY[val]
        return str(val)


################################################################################
# FEATURE PRESENTATION
################################################################################
class Feature(Item):
    _type = 'feature'
    _elements = (
        {'attr': 'count',             'type': int,        'limits': (1, 10),    'name': 'Count'},
        {'attr': 'showRatingBumper',  'type': strToBool,  'limits': LIMIT_BOOL, 'name': 'Show Rating Bumper'}
    )
    displayName = 'Feature'
    typeChar = 'F'

    def __init__(self):
        Item.__init__(self)
        self.count = 1
        self.showRatingBumper = True


################################################################################
# TRIVIA
################################################################################
class Trivia(Item):
    _type = 'trivia'
    _elements = (
        {'attr': 'count',       'type': int, 'limits': (1, 10), 'name': 'Count'},
        {'attr': 'qDuration',   'type': int, 'limits': (1, 30), 'name': 'Question Duration'},
        {'attr': 'cDuration',   'type': int, 'limits': (1, 30), 'name': 'Clue Duration'},
        {'attr': 'aDuration',   'type': int, 'limits': (1, 30), 'name': 'Answer Duration'}
    )
    displayName = 'Trivia Slides'
    typeChar = 'Q'

    def __init__(self):
        Item.__init__(self)
        self.count = 1
        self.qDuration = 10
        self.cDuration = 10
        self.aDuration = 10


################################################################################
# Trailer
################################################################################
class Trailer(Item):
    _type = 'trailer'
    _elements = (
        {'attr': 'count',  'type': int,  'limits': (1, 10), 'name': 'Count'},
        {'attr': 'source', 'type': None, 'limits': LIMIT_FILE,    'name': 'Source'}
    )
    displayName = 'Trailer'
    typeChar = 'T'

    def __init__(self):
        Item.__init__(self)
        self.count = 1
        self.source = ''

    def display(self):
        if self.count > 1:
            return '{0} x {1}'.format(self.displayName, self.count)
        return self.displayName


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
                'trivia.outro'
            ],
            'name': 'Type'
        },
        {
            'attr': 'source',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'Source'
        }
    )
    displayName = 'Video Bumper'
    typeChar = 'V'

    def __init__(self):
        Item.__init__(self)
        self.vtype = ''
        self.source = ''

    def display(self):
        if not self.vtype:
            return self.displayName
        return self.vtype.replace('.', ' ').title()


################################################################################
# AUDIOFORMAT
################################################################################
class AudioFormat(Item):
    _type = 'audioformat'
    _elements = (
        {
            'attr': 'format',
            'type': None,
            'limits': ['Dolby TrueHD', 'DTS-X', 'DTS-HD Master Audio', 'DTS', 'Dolby Atmos', 'THX', 'Dolby Digital Plus', 'Dolby Digital'],
            'name': 'Format'
        },
        {
            'attr': 'source',
            'type': None,
            'limits': LIMIT_FILE,
            'name': 'Source'
        },
    )
    displayName = 'Audio Format Bumper'
    typeChar = 'A'

    def __init__(self):
        Item.__init__(self)
        self.format = ''
        self.source = ''


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

    def getLimits(self, idx):
        e = self._elements[idx]
        if not e['attr'] == 'arg' or self.command not in ('skip', 'back'):
            return Item.getLimits(self, idx)

        return (1, 20)

    def getType(self, idx):
        e = self._elements[idx]
        if not e['attr'] == 'arg' or self.command not in ('skip', 'back'):
            return Item.getType(self, idx)

        return int

    def getSettingOptions(self, setting):
        if setting == 'arg':
            if self.command in ('back', 'skip'):
                return (0, 99)
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
        command = self.command and ' ({0}:{1})'.format(self.command, self.arg) or ''
        return '{0}{1}'.format(self.displayName, command)


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
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


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
    print path
    import xbmcvfs
    f = xbmcvfs.File(path, 'r')
    xmlString = f.read().decode('utf-8')
    f.close()
    return getItemsFromString(xmlString)
