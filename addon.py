import sys

if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1] or False
        print '[- CinemaVision -]: Passed args: {0}'.format(repr(sys.argv))

    if arg == 'trailer.clearWatched':
        from lib import settings
        settings.clearDBWatchedStatus()
    elif arg == 'trailer.clearBroken':
        from lib import settings
        settings.clearDBBrokenStatus()
    elif arg == 'experience':
        from lib import player
        player.begin()
    elif str(arg).startswith('movieid='):
        from lib import player
        player.begin(movieid=arg[8:])
    elif str(arg).startswith('episodeid='):
        from lib import player
        player.begin(episodeid=arg[10:])
    elif arg == 'selection':
        from lib import player
        player.begin(selection=True)
    elif arg == 'update.database':
        from lib import cvutil
        from lib import kodiutil
        cvutil.loadContent(from_settings=True)
        kodiutil.ADDON.openSettings()
    elif arg == 'feature.setRatingBumperStyle':
        from lib import cvutil
        cvutil.setRatingBumperStyle()
    elif arg == 'pastebin.paste.log':
        from lib import settings
        settings.pasteLog()
    elif arg == 'pastebin.delete.key':
        from lib import settings
        settings.deleteUserKey()
    elif arg == 'reset.database':
        from lib import settings
        settings.removeContentDatabase()
    elif str(arg).startswith('sequence.'):
        from lib import settings
        settings.setDefaultSequence(arg)
    else:
        from lib import main
        main.main()
