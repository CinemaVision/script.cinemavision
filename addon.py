import sys

if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1] or False

    if arg == 'trailer.clearWatched':
        from lib import settings
        settings.clearDBWatchedStatus()
    elif arg == 'experience':
        from lib import player
        player.begin()
    elif arg == 'update.database':
        from lib import cvutil
        cvutil.loadContent(from_settings=True)
    elif arg == 'feature.setRatingBumperStyle':
        from lib import cvutil
        cvutil.setRatingBumperStyle()
    else:
        from lib import main
        main.main()
