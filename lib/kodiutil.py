import xbmc
import xbmcaddon

ADDON_ID = 'script.cinemavision'
ADDON = xbmcaddon.Addon(ADDON_ID)

DEBUG = True


def translatePath(path):
    return xbmc.translatePath(path).decode('utf-8')

PROFILE_PATH = translatePath(ADDON.getAddonInfo('profile'))
ADDON_PATH = translatePath(ADDON.getAddonInfo('path'))


def LOG(msg):
    xbmc.log('CinemaVison: {0}'.format(msg))


def DEBUG_LOG(msg):
    if DEBUG:
        LOG(msg)


def ERROR(msg):
    if msg:
        LOG(msg)
    import traceback
    xbmc.log(traceback.format_exc())
