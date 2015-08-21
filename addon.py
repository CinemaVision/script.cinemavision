import sys

if __name__ == '__main__':
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1] or False

    if arg == 'trailer.clearWatched':
        from lib import settings
        settings.clearDBWatchedStatus()
    elif arg == 'experience':
        from lib import cvutil
        from lib import experience
        from lib import kodiutil

        seqPath = cvutil.getSequencePath()

        kodiutil.DEBUG_LOG('Loading sequence for 2D: {0}'.format(repr(seqPath)))

        e = experience.ExperiencePlayer().create(seqPath)
        e.start()
    else:
        from lib import main
        main.main()
