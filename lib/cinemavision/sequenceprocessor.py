import random
import database as DB
import sequence
import util
import scrapers


# Playabe is implemented as a dict to be easily serializable to JSON
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

    @duration.setter
    def duration(self, val):
        self['duration'] = val


class Video(Playable):
    type = 'VIDEO'

    def __init__(self, path, user_agent=''):
        self['path'] = path
        self['userAgent'] = user_agent

    @property
    def userAgent(self):
        return self['userAgent']


class Feature(Video):
    type = 'FEATURE'

    def __repr__(self):
        return 'FEATURE [ {0} ]:\n    Path: {1}\n    Rating ({2}): {3}\n    Genres: {4}\n    3D: {5}\n    Audio: {6}'.format(
            self.title,
            self.path,
            self.ratingSystem,
            self.rating,
            ', '.join(self.genres),
            self.is3D and 'Yes' or 'No',
            self.audioFormat
        )

    @property
    def title(self):
        return self.get('title', '')

    @title.setter
    def title(self, val):
        self['title'] = val

    @property
    def rating(self):
        return self.get('rating', '')

    @rating.setter
    def rating(self, val):
        self['rating'] = val

    @property
    def ratingSystem(self):
        return self.get('ratingSystem', '')

    @ratingSystem.setter
    def ratingSystem(self, val):
        self['ratingSystem'] = val

    @property
    def genres(self):
        return self.get('genres', [])

    @genres.setter
    def genres(self, val):
        self['genres'] = val

    @property
    def is3D(self):
        return self.get('is3D', False)

    @is3D.setter
    def is3D(self, val):
        self['is3D'] = val

    @property
    def audioFormat(self):
        return self.get('audioFormat', '')

    @audioFormat.setter
    def audioFormat(self, val):
        self['audioFormat'] = val


class FeatureHandler:
    def getRatingBumper(self, feature):
        try:
            return random.choice(
                [
                    x for x in DB.RatingsBumpers.select().where(
                        (DB.RatingsBumpers.system == feature.ratingSystem) &
                        (DB.RatingsBumpers.name == feature.rating) &
                        (DB.RatingsBumpers.is3D == feature.is3D)
                    )
                ]
            )
        except IndexError:
            return None

    def __call__(self, caller, sItem):
        features = caller.featureQueue[:sItem.count]
        caller.featureQueue = caller.featureQueue[sItem.count:]
        playables = []
        for f in features:
            bumper = self.getRatingBumper(f)
            if bumper:
                playables.append(Video(bumper.path))
            playables.append(f)

        return playables


class TriviaHandler:
    def __call__(self, caller, sItem):
        durationLimit = sItem.duration * 60
        totalDuration = 0
        ret = []
        durations = (sItem.qDuration, sItem.cDuration, sItem.cDuration, sItem.cDuration, sItem.aDuration)
        for trivia in DB.Trivia.select().order_by(DB.fn.Random()):
            paths = (trivia.questionPath, trivia.cluePath1, trivia.cluePath2, trivia.cluePath3, trivia.answerPath)
            slides = []
            for p, d in zip(paths, durations):
                if p:
                    slides.append(Image(p, d))
                    totalDuration += d
            if len(slides) == 1:  # This is a still set duration accordingly
                totalDuration -= slides[0].duration
                totalDuration += sItem.sDuration
                slides[0].duration = sItem.sDuration
            ret += slides
            if totalDuration >= durationLimit:
                break

        return ret


class TrailerHandler:
    def __init__(self):
        self.trailers = scrapers.getTrailers()
        self.caller = None

    def __call__(self, caller, sItem):
        self.caller = caller
        filtered = self.filter(self.trailers)

        trailers = random.sample(filtered, sItem.count)

        return [Video(t.getPlayableURL(), t.userAgent) for t in trailers]

    def filter(self, trailers):
        filtered = trailers

        if self.caller.ratings:
            filtered = [f for f in filtered if f.fullRating in self.caller.ratings]

        if self.caller.genres:
            filtered = [f for f in filtered if any(x in self.caller.genres for x in f.genres)]

        return filtered


class VideoBumperHandler:
    def __init__(self):
        self.caller = None
        self.handlers = {
            '3D.intro': self._3DIntro,
            '3D.outro': self._3DOutro,
            'countdown': self.countdown,
            'courtesy': self.courtesy,
            'feature.intro': self.featureIntro,
            'feature.outro': self.featureOutro,
            'intermission': self.intermission,
            'short.film': self.shortFilm,
            'theater.intro': self.theaterIntro,
            'theater.outro': self.theaterOutro,
            'trailers.intro': self.trailersIntro,
            'trailers.outro': self.trailersOutro,
            'trivia.intro': self.triviaIntro,
            'trivia.outro': self.triviaOutro
        }

    def __call__(self, caller, sItem):
        self.caller = caller
        return self.handlers[sItem.vtype](sItem)

    def defaultHandler(self, sItem):
        is3D = self.caller.currentFeature.is3D

        try:
            bumper = random.choice([x for x in DB.VideoBumpers.select().where((DB.VideoBumpers.type == sItem.vtype) & (DB.VideoBumpers.is3D == is3D))])
            return [Video(bumper.path)]
        except IndexError:
            pass
        return []

    def _3DIntro(self, sItem):
        return self.defaultHandler(sItem)

    def _3DOutro(self, sItem):
        return self.defaultHandler(sItem)

    def countdown(self, sItem):
        return self.defaultHandler(sItem)

    def courtesy(self, sItem):
        return self.defaultHandler(sItem)

    def featureIntro(self, sItem):
        return self.defaultHandler(sItem)

    def featureOutro(self, sItem):
        return self.defaultHandler(sItem)

    def intermission(self, sItem):
        return self.defaultHandler(sItem)

    def shortFilm(self, sItem):
        return self.defaultHandler(sItem)

    def theaterIntro(self, sItem):
        return self.defaultHandler(sItem)

    def theaterOutro(self, sItem):
        return self.defaultHandler(sItem)

    def trailersIntro(self, sItem):
        return self.defaultHandler(sItem)

    def trailersOutro(self, sItem):
        return self.defaultHandler(sItem)

    def triviaIntro(self, sItem):
        return self.defaultHandler(sItem)

    def triviaOutro(self, sItem):
        return self.defaultHandler(sItem)


class SequenceProcessor:
    def __init__(self, sequence_path):
        self.sequence = []
        self.featureQueue = []
        self.playables = []
        self.ratings = []
        self.genres = []
        self.loadSequence(sequence_path)
        self.createDefaultFeature()

    def empty(self):
        return not self.playables

    @property
    def currentFeature(self):
        return self.featureQueue and self.featureQueue[0] or self.defaultFeature

    def createDefaultFeature(self):
        self.defaultFeature = Feature('')
        self.defaultFeature.title = 'Default Feature'
        self.defaultFeature.rating = 'NR'
        self.defaultFeature.ratingSystem = 'MPAA'
        self.defaultFeature.audioFormat = 'THX'

    def addFeature(self, feature):
        if feature.rating:
            rating = '{0}:{1}'.format(feature.ratingSystem, feature.rating)
            if rating not in self.ratings:
                self.ratings.append(rating)

        if feature.genres:
            self.genres += feature.genres

        self.featureQueue.append(feature)

    def audioformatHandler(self, sItem):
        if sItem.source:
            return [Video(sItem.source)]
        bumper = None

        print self.currentFeature

        if self.currentFeature.audioFormat:
            try:
                bumper = random.choice([x for x in DB.AudioFormatBumpers.select().where(DB.AudioFormatBumpers.format == self.currentFeature.audioFormat)])
                util.DEBUG_LOG('Using bumper based on feature codec info ({0})'.format(self.currentFeature.title))
            except IndexError:
                pass

        if sItem.format:
            try:
                bumper = random.choice([x for x in DB.AudioFormatBumpers.select().where(DB.AudioFormatBumpers.format == sItem.format)])
                util.DEBUG_LOG('Using bumper based on setting ({0})'.format(self.currentFeature.title))
            except IndexError:
                pass

        if bumper:
            return [Video(bumper.path)]

        return []

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
        'feature': FeatureHandler(),
        'trivia': TriviaHandler(),
        'trailer': TrailerHandler(),
        'video': VideoBumperHandler(),
        'audioformat': audioformatHandler,
        'action': actionHandler,
        'command': commandHandler
    }

    def process(self):
        util.DEBUG_LOG('Processing sequence...')
        util.DEBUG_LOG('Feature count: {0}'.format(len(self.featureQueue)))
        util.DEBUG_LOG('Ratings: {0}'.format(', '.join(self.ratings)))
        util.DEBUG_LOG('Genres: {0}'.format(', '.join(self.genres)))

        util.DEBUG_LOG('\n\n' + '\n\n'.join([str(f) for f in self.featureQueue]))

        self.playables = []
        pos = 0
        while pos < len(self.sequence):
            sItem = self.sequence[pos]

            if not sItem.enabled:
                pos += 1
                continue

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
        self.playables.append(None)  # Keeps it from being empty until AFTER the last item
        util.DEBUG_LOG('Sequence processing finished')

    def loadSequence(self, sequence_path):
        self.sequence = sequence.loadSequence(sequence_path)

    def next(self):
        if not self.playables:
            return None

        return self.playables.pop(0)
