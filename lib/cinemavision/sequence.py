from xml.etree import ElementTree as ET


################################################################################
# BASE class for all content items
################################################################################
class Item:
    _tag = 'item'   # XML tag when serialized
    _type = 'BASE'  # Name of the type of content. Equal to the xml tag type attribute when serialized
    _elements = ()  # Tuple of attributes to serialize

    def toNode(self):
        item = ET.Element(self._tag)
        item.set('type', self._type)
        for e in self._elements:
            sub = ET.Element(e)
            sub.text = getattr(self, e)
            item.append(sub)
        return item

    @staticmethod
    def fromNode(node):
        itype = node.attrib('type')
        if itype in CONTENT_CLASSES:
            return CONTENT_CLASSES[itype]._fromNode(node)

    @classmethod
    def _fromNode(cls, node):
        new = cls()
        for e in new._elements:
            sub = node.find(e)
            if sub:
                setattr(new, e, sub.text)


################################################################################
# FEATURE PRESENTATION
################################################################################
class Feature(Item):
    _type = 'feature'


################################################################################
# TRIVIA
################################################################################
class Trivia(Item):
    _type = 'trivia'
    _elements = ('count', 'qDuration', 'cDuration', 'aDuration')

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
    _elements = ('count', 'source')

    def __init__(self):
        self.count = 1
        self.source = ''


################################################################################
# VIDEO
################################################################################
class Video(Item):
    _type = 'video'
    _elements = ('source')

    def __init__(self):
        self.source = ''


################################################################################
# RATING
################################################################################
class Rating(Video):
    _type = 'rating'


################################################################################
# FORMAT
################################################################################
class Format(Video):
    _type = 'format'


################################################################################
# INTERMISSION
################################################################################
class Intermission(Video):
    _type = 'intermission'
    _elements = ('count', 'source')

    def __init__(self):
        self.count = 1
        self.source = ''


CONTENT_CLASSES = {
    'trivia':   Trivia,
    'trailer':  Trailer
}
