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

        e = experience.ExperiencePlayer().create()

        seqPath = cvutil.getSequencePath(for_3D=e.has3D)

        kodiutil.DEBUG_LOG('Loading sequence for {0}: {1}'.format(e.has3D and '3D' or '2D', repr(seqPath)))

        e.start(seqPath)
    else:
        from lib import main
        main.main()
