from peewee import peewee
import util

DB = peewee.SqliteDatabase(util.pathJoin(util.STORAGE_PATH, 'content.db'))

util.callback(None, 'Creating/updating database...')


class ContentBase(peewee.Model):
    name = peewee.CharField()
    accessed = peewee.IntegerField(default=0)
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

util.callback(' - CinemaSpots')


class VideoBumpers(ContentBase):
    type = peewee.CharField()
    is3D = peewee.BooleanField()

    rating = peewee.CharField(null=True)
    genre = peewee.CharField(null=True)
    year = peewee.CharField(null=True)

    path = peewee.CharField(unique=True)

VideoBumpers.create_table(fail_silently=True)

util.callback(None, 'Database created')
