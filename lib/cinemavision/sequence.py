from xml.etree import ElementTree as ET
import xml.dom.minidom as minidom


################################################################################
# BASE class for all content items
################################################################################
class Item:
    _tag = 'item'   # XML tag when serialized
    _type = 'BASE'  # Name of the type of content. Equal to the xml tag type attribute when serialized
    _elements = ()  # Tuple of attributes to serialize
    displayName = ''
    typeChar = ''

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
        for e in self._elements:
            sub = ET.Element(e['attr'])
            sub.text = str(getattr(self, e['attr']))
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
        for e in new._elements:
            sub = node.find(e['attr'])
            if sub is not None:
                new._set(e['attr'], sub.text)
        return new

    def elementData(self, element_name):
        for e in self._elements:
            if element_name == e['attr']:
                return e

    def getSettingOptions(self, setting):
        limits = self.elementData(setting)['limits']
        return limits or ''

    def setSetting(self, setting, value):
        setattr(self, setting, value)

    def getSetting(self, setting):
        return getattr(self, setting)

    def getSettingIndex(self, setting):
        for i, e in enumerate(self._elements):
            if e['attr'] == setting:
                return i

    def display(self):
        return self.displayName


################################################################################
# FEATURE PRESENTATION
################################################################################
class Feature(Item):
    _type = 'feature'
    displayName = 'Feature'
    typeChar = 'F'


################################################################################
# TRIVIA
################################################################################
class Trivia(Item):
    _type = 'trivia'
    _elements = (
        {'attr': 'count',       'type': int, 'limits': (1, 10), 'name': 'Count'},
        {'attr': 'qDuration',   'type': int, 'limits': (1, 60), 'name': 'Question Duration'},
        {'attr': 'cDuration',   'type': int, 'limits': (1, 60), 'name': 'Clue Duration'},
        {'attr': 'aDuration',   'type': int, 'limits': (1, 60), 'name': 'Answer Duration'}
    )
    displayName = 'Trivia Slide'
    typeChar = 'Q'

    def __init__(self):
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
        {'attr': 'source', 'type': None, 'limits': None,    'name': 'Source'}
    )
    displayName = 'Trailer'
    typeChar = 'T'

    def __init__(self):
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
        {'attr': 'source', 'type': None, 'limits': None,    'name': 'Source'},
    )
    displayName = 'Video Bumper'
    typeChar = 'V'

    def __init__(self):
        self.source = ''


################################################################################
# AUDIOFORMAT
################################################################################
class AudioFormat(Video):
    _type = 'audioformat'
    displayName = 'Audio Format Bumper'
    typeChar = 'A'


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
            'limits': ['back', ],
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
            'limits': ['feature.queue=full', 'none'],
            'name': 'Condition'
        }
    )
    displayName = 'Command'
    typeChar = 'C'

    def _set(self, attr, value):
        if self.command == 'back':
            if attr == 'arg':
                value = int(value)
        Item._set(self, attr, value)

    def __init__(self):
        self.command = ''
        self.arg = ''
        self.condition = ''

    def getSettingOptions(self, setting):
        if setting == 'command':
            return self.elementData('command')['limits']
        elif setting == 'condition':
            return self.elementData('condition')['limits']
        elif setting == 'arg':
            if self.command == 'back':
                return (0, 99)

    def setSetting(self, setting, value):
        Item.setSetting(self, setting, value)

        if setting == 'command':
            if self.command == 'back':
                if not self.condition:
                    self.condition = 'feature.queue=full'
                if not self.arg:
                    self.arg = 2
            else:
                self.condition = ''

    def getSetting(self, setting):
        if self.command == 'back':
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
    ('Q', 'Trivia Slide', 'Q', Trivia),
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
