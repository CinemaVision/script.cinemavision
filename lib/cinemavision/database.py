import time
import datetime

try:
    datetime.datetime.strptime('0', '%H')
except TypeError:
    # Fix for datetime issues with XBMC/Kodi
    class new_datetime(datetime.datetime):
        @classmethod
        def strptime(cls, dstring, dformat):
            return datetime.datetime(*(time.strptime(dstring, dformat)[0:6]))

    datetime.datetime = new_datetime

from peewee import peewee
import util

fn = peewee.fn

util.callback(None, 'Creating/updating database...')


###########################################################################################
# Watched Database
###########################################################################################
DB = peewee.SqliteDatabase(util.pathJoin(util.STORAGE_PATH, 'content.db'))


class ContentBase(peewee.Model):
    name = peewee.CharField()
    accessed = peewee.DateTimeField(null=True)
    pack = peewee.TextField(null=True)

    class Meta:
        database = DB

util.callback(' - Music')


class Song(ContentBase):
    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    path = peewee.CharField(unique=True)

Song.create_table(fail_silently=True)

util.callback(' - Tivia')


class Trivia(ContentBase):
    type = peewee.CharField()

    TID = peewee.CharField(unique=True)

    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    questionPath = peewee.CharField(unique=True, null=True)
    cluePath1 = peewee.CharField(unique=True, null=True)
    cluePath2 = peewee.CharField(unique=True, null=True)
    cluePath3 = peewee.CharField(unique=True, null=True)
    answerPath = peewee.CharField(unique=True, null=True)

Trivia.create_table(fail_silently=True)

util.callback(' - AudioFormatBumpers')


class AudioFormatBumpers(ContentBase):
    is3D = peewee.BooleanField(default=False)
    format = peewee.CharField()
    path = peewee.CharField(unique=True)

AudioFormatBumpers.create_table(fail_silently=True)

util.callback(' - RatingsBumpers')


class RatingsBumpers(ContentBase):
    is3D = peewee.BooleanField(default=False)
    system = peewee.CharField(default='MPAA')
    path = peewee.CharField(unique=True)

RatingsBumpers.create_table(fail_silently=True)

util.callback(' - VideoBumpers')


class VideoBumpers(ContentBase):
    type = peewee.CharField()
    is3D = peewee.BooleanField()

    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    path = peewee.CharField(unique=True)

VideoBumpers.create_table(fail_silently=True)


###########################################################################################
# Watched Database
###########################################################################################
W_DB = peewee.SqliteDatabase(util.pathJoin(util.STORAGE_PATH, 'watched.db'))


class WatchedBase(peewee.Model):
    WID = peewee.CharField(unique=True)
    watched = peewee.BooleanField(default=False)
    date = peewee.DateTimeField(default=datetime.date(1900, 1, 1))

    class Meta:
        database = W_DB


class WatchedTrailers(WatchedBase):
    source = peewee.CharField()
    rating = peewee.CharField(null=True)
    genres = peewee.CharField(null=True)
    title = peewee.CharField()
    url = peewee.CharField()
    userAgent = peewee.CharField(null=True)


WatchedTrailers.create_table(fail_silently=True)


util.callback(' - Trailers (watched status)')


class WatchedTrivia(WatchedBase):
    pass


WatchedTrivia.create_table(fail_silently=True)

util.callback(' - Trivia (watched status)')

util.callback(None, 'Database created')
