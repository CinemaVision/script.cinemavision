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

    @property
    def fileChar(self):
        return self.typeChar

    def toNode(self):
        item = ET.Element(self._tag)
        item.set('type', self._type)
        for e, conv in self._elements:
            sub = ET.Element(e)
            sub.text = str(getattr(self, e))
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
        for e, conv in new._elements:
            sub = node.find(e[0])
            if sub:
                setattr(new, e, conv and conv(sub.text) or sub.text)
        return new


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
    _elements = (('count', int), ('qDuration', int), ('cDuration', int), ('aDuration', int))
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
    _elements = (('count', int), ('source', None))
    displayName = 'Trailer'
    typeChar = 'T'

    def __init__(self):
        self.count = 1
        self.source = ''


################################################################################
# VIDEO
################################################################################
class Video(Item):
    _type = 'video'
    _elements = (('source', None), )
    displayName = 'Video'
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
    displayName = 'Command'
    typeChar = 'C'


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
