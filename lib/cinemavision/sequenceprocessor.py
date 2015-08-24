import random
import time
import datetime
import database as DB
import sequence
import util
import scrapers
import ratings


# Playabe is implemented as a dict to be easily serializable to JSON
class Playable(dict):
    type = None

    @property
    def path(self):
        return self['path']

    def __repr__(self):
        return '{0}: {1}'.format(self.type, repr(self.path))


class Image(Playable):
    type = 'IMAGE'

    def __init__(self, path, duration=10, set_number=0, set_id=None, *args, **kwargs):
        Playable.__init__(self, *args, **kwargs)
        self['path'] = path
        self['duration'] = duration
        self['setNumber'] = set_number
        self['setID'] = set_id

    def __repr__(self):
        return 'IMAGE ({0}s): {1}'.format(self.duration, self.path)

    @property
    def setID(self):
        return self['setID']

    @property
    def duration(self):
        return self['duration']

    @duration.setter
    def duration(self, val):
        self['duration'] = val

    @property
    def setNumber(self):
        return self['setNumber']


class Song(Playable):
    type = 'SONG'

    def __init__(self, path, duration=0, *args, **kwargs):
        self['path'] = path
        self['duration'] = duration
        Playable.__init__(self, *args, **kwargs)

    @property
    def duration(self):
        return self['duration']

    @property
    def durationInt(self):
        return int(self['duration'])


class ImageQueue(dict):
    type = 'IMAGE.QUEUE'

    def __init__(self, handler, s_item, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._handler = handler
        self.sItem = s_item
        self.maxDuration = s_item.getLive('duration') * 60
        self.pos = -1
        self.transition = None
        self.transitionDuration = 400
        self.music = None
        self.musicVolume = 85
        self.musicFadeIn = 3.0
        self.musicFadeOut = 3.0

    def __iadd__(self, other):
        for o in other:
            self.duration += o.duration

        self.queue += other
        return self

    def __contains__(self, images):
        paths = [i.path for i in self.queue]
        if isinstance(images, list):
            for i in images:
                if i.path in paths:
                    return True
        else:
            return images.path in paths

        return False

    def __repr__(self):
        return '{0}: {1}secs'.format(self.type, self.duration)

    def reset(self):
        self.pos = -1

    def size(self):
        return len(self.queue)

    @property
    def duration(self):
        return self.get('duration', 0)

    @duration.setter
    def duration(self, val):
        self['duration'] = val

    @property
    def queue(self):
        return self.get('queue', [])

    @queue.setter
    def queue(self, q):
        self['queue'] = q

    def current(self):
        return self.queue[self.pos]

    def add(self, image):
        self.queue.append(image)

    def next(self, start=0, extend=False):
        overtime = start and time.time() - start >= self.maxDuration
        if overtime and not self.current().setNumber:
            return None

        if self.pos >= self.size() - 1:
            if extend or not overtime:
                return self._next()
            else:
                return None

        self.pos += 1

        return self.queue[self.pos]

    def _next(self):
        util.DEBUG_LOG('ImageQueue: Requesting next...')
        images = self._handler.next(self)
        if not images:
            util.DEBUG_LOG('ImageQueue: No next images')
            return None

        util.DEBUG_LOG('ImageQueue: {0} returned'.format(len(images)))
        self.queue += images
        self.pos += 1

        return self.current()

    def prev(self):
        if self.pos < 1:
            return None
        self.pos -= 1

        return self.current()

    def mark(self, image):
        if not image.setNumber:
            util.DEBUG_LOG('ImageQueue: Marking image as watched')
            self._handler.mark(image)

    def onFirst(self):
        return self.pos == 0

    def onLast(self):
        return self.pos == self.size() - 1


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
            repr(self.title),
            repr(self.path),
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
        count = sItem.getLive('count')

        util.DEBUG_LOG('[F] x {0}'.format(count))

        features = caller.featureQueue[:count]
        caller.featureQueue = caller.featureQueue[count:]
        playables = []
        showRatingBumper = sItem.getLive('showRatingBumper')
        for f in features:
            if showRatingBumper:
                bumper = self.getRatingBumper(f)
                if bumper:
                    playables.append(Video(bumper.path))
            playables.append(f)

        return playables


class TriviaHandler:
    def __init__(self):
        pass

    def __call__(self, caller, sItem):
        duration = sItem.getLive('duration')

        util.DEBUG_LOG('[Q] {0}m'.format(duration))

        durationLimit = duration * 60
        queue = ImageQueue(self, sItem)
        queue.transition = sItem.getLive('transition')
        queue.transitionDuration = sItem.getLive('transitionDuration')

        for slides in self.getTriviaImages(sItem):
            queue += slides

            if queue.duration >= durationLimit:
                break

        self.addMusic(sItem, queue)

        return [queue]

    def addMusic(self, sItem, queue):
        mode = sItem.getLive('music')
        if mode == 'off':
            return

        if mode == 'content':
            queue.music = [Song(s.path, s.duration) for s in DB.Song.select().order_by(DB.fn.Random())]
        elif mode == 'dir':
            path = sItem.getLive('musicDir')
            if not path:
                return

            import mutagen
            mutagen.setFileOpener(util.vfs.File)

            queue.music = []
            for p in util.listFilePaths(path):
                data = mutagen.File(p)
                d = 0
                if data:
                    d = data.info.length
                queue.music.append(Song(p, d))

            random.shuffle(queue.music)

        duration = sum([s.duration for s in queue.music])

        if duration:  # Maybe they were all zero - we'll be here forever :)
            while duration < queue.duration:
                for i in range(len(queue.music)):
                    song = queue.music[i]
                    duration += song.duration
                    queue.music.append(song)
                    if duration >= queue.duration:
                        break

        queue.musicVolume = util.getSettingDefault('trivia.musicVolume')
        queue.musicFadeIn = util.getSettingDefault('trivia.musicFadeIn')
        queue.musicFadeOut = util.getSettingDefault('trivia.musicFadeOut')

    def getTriviaImages(self, sItem):
        # Do this each set in reverse so the setNumber counts down
        durations = (
            sItem.getLive('aDuration'),
            sItem.getLive('cDuration'),
            sItem.getLive('cDuration'),
            sItem.getLive('cDuration'),
            sItem.getLive('qDuration')
        )
        for trivia in DB.Trivia.select().order_by(DB.fn.Random()):
            try:
                DB.WatchedTrivia.get((DB.WatchedTrivia.WID == trivia.TID) & DB.WatchedTrivia.watched)
            except DB.peewee.DoesNotExist:
                yield self.createTriviaImages(sItem, trivia, durations)

        # Grab the oldest 4 trivias, shuffle and yield... repeat
        pool = []
        for watched in DB.WatchedTrivia.select().where(DB.WatchedTrivia.watched).order_by(DB.WatchedTrivia.date):
            try:
                trivia = DB.Trivia.get(DB.Trivia.TID == watched.WID)
            except DB.peewee.DoesNotExist:
                continue
            pool.append(trivia)

            if len(pool) > 3:
                random.shuffle(pool)
                for t in pool:
                    yield self.createTriviaImages(sItem, t, durations)
                pool = []

        if pool:
            random.shuffle(pool)
            for t in pool:
                yield self.createTriviaImages(sItem, t, durations)

    def createTriviaImages(self, sItem, trivia, durations):
        paths = (trivia.answerPath, trivia.cluePath3, trivia.cluePath2, trivia.cluePath1, trivia.questionPath)
        slides = []
        setNumber = 0
        for p, d in zip(paths, durations):
            if p:
                slides.append(Image(p, d, setNumber, trivia.TID))
                setNumber += 1

        slides.reverse()  # Slides are backwards

        if len(slides) == 1:  # This is a still - set duration accordingly
            slides[0].duration = sItem.getLive('sDuration')

        return slides

    def next(self, image_queue):
        for slides in self.getTriviaImages(image_queue.sItem):
            if slides not in image_queue:
                return slides
        return None

    def mark(self, image):
        trivia = DB.WatchedTrivia.get_or_create(WID=image.setID)[0]
        trivia.update(
            watched=True,
            date=datetime.datetime.now()
        ).where(DB.WatchedTrivia.WID == image.setID).execute()


class TrailerHandler:
    def __init__(self):
        self.caller = None

    def __call__(self, caller, sItem):
        self.caller = caller

        source = sItem.getLive('source')

        playables = []
        if source == 'itunes':
            playables = self.iTunesHandler(sItem)
        elif source == 'dir':
            playables = self.dirHandler(sItem)
        elif source == 'file':
            playables = self.fileHandler(sItem)

        if not playables:
            util.DEBUG_LOG('[T] {0}: NOT SHOWING'.format(source))

        return playables

    def filter(self, sItem, trailers):
        filtered = trailers
        globalRatingLimit = util.getSettingDefault('trailer.globalRatingLimit')

        if globalRatingLimit:
            util.DEBUG_LOG('    - Limited by rating: {0}'.format(globalRatingLimit.name))
            filtered = [f for f in filtered if ratings.getRating(f.fullRating).value <= globalRatingLimit.value]
        else:
            if sItem.getLive('limitRating'):
                if self.caller.ratings:
                    util.DEBUG_LOG('    - Filtering by rating')
                    filtered = [f for f in filtered if f.fullRating in self.caller.ratings]

        if sItem.getLive('limitGenre'):
            if self.caller.genres:
                util.DEBUG_LOG('    - Filtering by genres')
                filtered = [f for f in filtered if any(x in self.caller.genres for x in f.genres)]

        return filtered

    def unwatched(self, trailers):
        ret = []
        for t in trailers:
            try:
                DB.WatchedTrailers.get((DB.WatchedTrailers.WID == t.ID) & DB.WatchedTrailers.watched)
            except DB.peewee.DoesNotExist:
                ret.append(t)

        return ret

    def convertItunesURL(self, url, res):
        repl = None
        for r in ('h480p', 'h720p', 'h1080p'):
            if r in url:
                repl = r
                break
        if not repl:
            return url

        return url.replace(repl, 'h{0}'.format(res))

    def oldest(self, sItem):
        util.DEBUG_LOG('    - All iTunes trailers watched - using oldest trailers')

        if sItem.getLive('limitRating') and self.caller.ratings:
            trailers = [t for t in DB.WatchedTrailers.select().where(DB.WatchedTrailers.rating << self.caller.ratings).order_by(DB.WatchedTrailers.date)]
        else:
            trailers = [t for t in DB.WatchedTrailers.select().order_by(DB.WatchedTrailers.date)]

        if not trailers:
            return []
        # Take the oldest for count + a few to make the random more random
        if sItem.getLive('limitGenre'):
            if self.caller.genres:
                trailers = [t for t in trailers if any(x in self.caller.genres for x in (t.genres or '').split(','))]
        count = sItem.getLive('count')
        if len(trailers) > count:
            trailers = random.sample(trailers[:count + 5], count)

        now = datetime.datetime.now()

        for t in trailers:
            DB.WatchedTrailers.update(
                watched=True,
                date=now
            ).where(DB.WatchedTrailers.WID == t.WID).execute()

        globalRatingLimit = util.getSettingDefault('trailer.globalRatingLimit')

        if globalRatingLimit:
            trailers = [t for t in trailers if ratings.getRating(t.rating).value <= globalRatingLimit.value]

        return [Video(self.convertItunesURL(t.url, sItem.getLive('quality')), t.userAgent) for t in trailers]

    def iTunesHandler(self, sItem):
        count = sItem.getLive('count')

        util.DEBUG_LOG('[T] iTunes x {0}'.format(count))

        trailers = scrapers.getTrailers()
        trailers = self.filter(sItem, trailers)
        if util.getSettingDefault('trailer.playUnwatched'):
            util.DEBUG_LOG('    - Filtering out watched')
            trailers = self.unwatched(trailers)

        if not trailers:
            return self.oldest(sItem)

        if len(trailers) > count:
            trailers = random.sample(trailers, count)

        now = datetime.datetime.now()
        quality = sItem.getLive('quality')

        for t in trailers:
            try:
                trailer = DB.WatchedTrailers.get(DB.WatchedTrailers.WID == t.ID)
                trailer.update(
                    source='itunes',
                    watched=True,
                    date=now,
                    title=t.title,
                    url=t.getPlayableURL(quality),
                    userAgent=t.userAgent,
                    rating=t.fullRating,
                    genres=','.join(t.genres)
                ).execute()
            except DB.peewee.DoesNotExist:
                DB.WatchedTrailers.create(
                    WID=t.ID,
                    source='itunes',
                    watched=True,
                    date=now,
                    title=t.title,
                    url=t.getPlayableURL(quality),
                    userAgent=t.userAgent,
                    rating=t.fullRating,
                    genres=','.join(t.genres)
                )

        return [Video(t.getPlayableURL(quality), t.userAgent) for t in trailers]

    def dirHandler(self, sItem):
        if not sItem.dir:
            return []

        count = sItem.getLive('count')

        util.DEBUG_LOG('[T] Directory x {0}'.format(count))

        try:
            files = util.vfs.listdir(sItem.dir)
            files = random.sample(files, count)
            return [Video(util.pathJoin(sItem.dir, p)) for p in files]
        except:
            util.ERROR()
            return []

    def fileHandler(self, sItem):
        if not sItem.file:
            return []

        util.DEBUG_LOG('[T] File: '.format(sItem.file))

        return [Video(sItem.file)]


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
            'trivia.outro': self.triviaOutro,
            'file': self.file
        }

    def __call__(self, caller, sItem):
        self.caller = caller
        playables = self.handlers[sItem.vtype](sItem)
        util.DEBUG_LOG('[V] {0}{1}'.format(sItem.vtype, not playables and ': NOT SHOWING' or ''))
        return playables

    def defaultHandler(self, sItem):
        is3D = self.caller.currentFeature.is3D and sItem.play3D

        if sItem.random:
            try:
                bumper = random.choice([x for x in DB.VideoBumpers.select().where((DB.VideoBumpers.type == sItem.vtype) & (DB.VideoBumpers.is3D == is3D))])
                return [Video(bumper.path)]
            except IndexError:
                pass

            if is3D and util.getSettingDefault('bumper.fallback2D'):
                try:
                    bumper = random.choice([x for x in DB.VideoBumpers.select().where((DB.VideoBumpers.type == sItem.vtype))])
                    return [Video(bumper.path)]
                except IndexError:
                    pass
        else:
            if sItem.source:
                return [Video(sItem.source)]

        return []

    def _3DIntro(self, sItem):
        if not self.caller.currentFeature.is3D:
            return []
        return self.defaultHandler(sItem)

    def _3DOutro(self, sItem):
        if not self.caller.currentFeature.is3D:
            return []
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

    def file(self, sItem):
        if sItem.file:
            return [Video(sItem.file)]
        else:
            return []


class AudioFormatHandler:
    def __call__(self, caller, sItem):
        bumper = None
        method = sItem.getLive('method')
        fallback = sItem.getLive('fallback')
        format_ = sItem.getLive('format')

        util.DEBUG_LOG('[A] Method: {0} Fallback: {1} Format: {2}'.format(method, fallback, format_))

        is3D = caller.currentFeature.is3D and sItem.play3D

        if method == 'af.detect':
            if caller.currentFeature.audioFormat:
                try:
                    bumper = random.choice(
                        [x for x in DB.AudioFormatBumpers.select().where(
                            (DB.AudioFormatBumpers.format == caller.currentFeature.audioFormat) & (DB.AudioFormatBumpers.is3D == is3D)
                        )]
                    )
                    util.DEBUG_LOG('    - Using bumper based on feature codec info ({0})'.format(caller.currentFeature.title))
                except IndexError:
                    if is3D and util.getSettingDefault('bumper.fallback2D'):
                        try:
                            bumper = random.choice(
                                [x for x in DB.AudioFormatBumpers.select().where(DB.AudioFormatBumpers.format == caller.currentFeature.audioFormat)]
                            )
                            util.DEBUG_LOG('    - Using bumper based on feature codec info and falling back to 2D ({0})'.format(caller.currentFeature.title))
                        except IndexError:
                            pass

        if (
            format_ and not bumper and (
                method == 'af.format' or (
                    method == 'af.detect' and fallback == 'af.format'
                )
            )
        ):
            try:
                bumper = random.choice(
                    [x for x in DB.AudioFormatBumpers.select().where(
                        (DB.AudioFormatBumpers.format == format_) & (DB.AudioFormatBumpers.is3D == is3D)
                    )]
                )
                util.DEBUG_LOG('    - Using bumper based on format setting ({0})'.format(repr(caller.currentFeature.title)))
            except IndexError:
                if is3D and util.getSettingDefault('bumper.fallback2D'):
                    try:
                        bumper = random.choice([x for x in DB.AudioFormatBumpers.select().where(DB.AudioFormatBumpers.format == format_)])
                        util.DEBUG_LOG('    - Using bumper based on format setting and falling back to 2D ({0})'.format(caller.currentFeature.title))
                    except IndexError:
                        pass
        if (
            sItem.file and not bumper and (
                method == 'af.file' or (
                    method == 'af.detect' and fallback == 'af.file'
                )
            )
        ):
            util.DEBUG_LOG('    - Using bumper based on file setting ({0})'.format(caller.currentFeature.title))
            return [Video(sItem.file)]

        if bumper:
            return [Video(bumper.path)]

        return []


class SequenceProcessor:
    def __init__(self, sequence_path):
        self.pos = -1
        self.size = 0
        self.sequence = []
        self.featureQueue = []
        self.playables = []
        self.ratings = []
        self.genres = []
        self.loadSequence(sequence_path)
        self.createDefaultFeature()

    def atEnd(self):
        return self.pos >= self.end

    @property
    def currentFeature(self):
        return self.featureQueue and self.featureQueue[0] or self.defaultFeature

    def createDefaultFeature(self):
        self.defaultFeature = Feature('')
        self.defaultFeature.title = 'Default Feature'
        self.defaultFeature.rating = 'NR'
        self.defaultFeature.ratingSystem = 'MPAA'
        self.defaultFeature.audioFormat = 'Other'

    def addFeature(self, feature):
        if feature.rating:
            rating = '{0}:{1}'.format(feature.ratingSystem, feature.rating)
            if rating not in self.ratings:
                self.ratings.append(rating)

        if feature.genres:
            self.genres += feature.genres

        self.featureQueue.append(feature)

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
        'audioformat': AudioFormatHandler(),
        'action': actionHandler,
        'command': commandHandler
    }

    def process(self):
        util.DEBUG_LOG('Processing sequence...')
        util.DEBUG_LOG('Feature count: {0}'.format(len(self.featureQueue)))
        util.DEBUG_LOG('Ratings: {0}'.format(', '.join(self.ratings)))
        util.DEBUG_LOG('Genres: {0}'.format(', '.join(self.genres)))

        if self.featureQueue:
            util.DEBUG_LOG('\n\n' + '\n\n'.join([str(f) for f in self.featureQueue]))
        else:
            util.DEBUG_LOG('NO FEATURES QUEUED')

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
        self.end = len(self.playables) - 1
        util.DEBUG_LOG('Sequence processing finished')

    def loadSequence(self, sequence_path):
        self.sequence = sequence.loadSequence(sequence_path)

    def next(self):
        if self.atEnd():
            return None

        self.pos += 1
        playable = self.playables[self.pos]

        return playable

    def prev(self):
        if self.pos > 0:
            self.pos -= 1

        playable = self.playables[self.pos]

        return playable
