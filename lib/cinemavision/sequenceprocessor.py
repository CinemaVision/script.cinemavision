import random
import database as DB
import sequence
import util


# Playabe is implemented a s dict to be easily serializable to JSON
class Playable(dict):
    type = None

    @property
    def path(self):
        return self['path']

    def __repr__(self):
        return '{0}: {1}'.format(self.type, self.path)


class Image(Playable):
    type = 'IMAGE'

    def __init__(self, path, duration=10):
        self['path'] = path
        self['duration'] = duration

    def __repr__(self):
        return 'IMAGE ({0}s): {1}'.format(self.duration, self.path)

    @property
    def duration(self):
        return self['duration']


class Video(Playable):
    type = 'VIDEO'

    def __init__(self, path):
        self['path'] = path


class SequenceProcessor:
    def __init__(self, sequence_path):
        self.sequence = []
        self.featureQueue = []
        self.playables = []
        self.loadSequence(sequence_path)

    def empty(self):
        return not self.playables

    def addFeature(self, path):
        self.featureQueue.append(Video(path))

    # SEQUENCE ITEM HANDLERS
    def videoHandler(self, sItem):
        # 'trivia.intro',
        # 'trivia.outro',
        # 'theater.intro',
        # 'theater.outro',
        # 'coming.attractions.intro',
        # 'coming.attractions.outro',
        # 'countdown',
        # 'feature.intro',
        # 'feature.outro',
        # 'intermission'
        return [Playable({'path': sItem.display()})]

    def triviaHandler(self, sItem):
        trivia = random.choice([x for x in DB.Trivia.select()])
        ret = []
        for i in (trivia.questionPath, trivia.cluePath1, trivia.cluePath2, trivia.cluePath3, trivia.answerPath):
            if i:
                ret.append(Image(i))
        return ret

    def trailerHandler(self, sItem):
        return []

    def featureHandler(self, sItem):
        playables = self.featureQueue[:sItem.count]
        self.featureQueue = self.featureQueue[sItem.count:]
        return playables

    def audioformatHandler(self, sItem):
        if sItem.source:
            return [sItem.source]
        elif sItem.format:
            bumper = random.choice([x for x in DB.AudioFormatBumpers.select().where(DB.AudioFormatBumpers.format == sItem.format)])
        return [Video(bumper.path)]

    def actionHandler(self, sItem):
        return []

    def commandHandler(self, sItem):
        if sItem.condition == 'feature.queue=full' and not self.featureQueue:
            return 0
        if sItem.condition == 'feature.queue=empty' and self.featureQueue:
            return 0
        if sItem.command == 'back':
            return sItem.arg * -1
        elif sItem.command == 'skip':
            return sItem.arg

    # SEQUENCE PROCESSING
    handlers = {
        'feature': featureHandler,
        'trivia': triviaHandler,
        'trailer': trailerHandler,
        'video': videoHandler,
        'audioformat': audioformatHandler,
        'action': actionHandler,
        'command': commandHandler
    }

    def process(self):
        util.DEBUG_LOG('Processing sequence...')
        self.playables = []
        pos = 0
        while pos < len(self.sequence):
            sItem = self.sequence[pos]
            handler = self.handlers.get(sItem._type)
            if handler:
                if sItem._type == 'command':
                    offset = handler(self, sItem)
                    pos += offset
                    if offset:
                        continue
                else:
                    self.playables += handler(self, sItem)

            pos += 1
        util.DEBUG_LOG('Sequence processing finished')

    def loadSequence(self, sequence_path):
        self.sequence = sequence.loadSequence(sequence_path)

    def next(self):
        if not self.playables:
            return None

        return self.playables.pop(0)
