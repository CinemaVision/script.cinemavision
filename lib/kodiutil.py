import time
import json
import binascii

import xbmc
import xbmcgui
import xbmcaddon

ADDON_ID = 'script.cinemavision'
ADDON = xbmcaddon.Addon(ADDON_ID)

DEBUG = True


def translatePath(path):
    return xbmc.translatePath(path).decode('utf-8')

PROFILE_PATH = translatePath(ADDON.getAddonInfo('profile'))
ADDON_PATH = translatePath(ADDON.getAddonInfo('path'))


def LOG(msg):
    xbmc.log('[- CinemaVison -]: {0}'.format(msg))


def DEBUG_LOG(msg):
    if DEBUG:
        LOG(msg)


def ERROR(msg=''):
    if msg:
        LOG(msg)
    import traceback
    xbmc.log(traceback.format_exc())


def getSetting(key, default=None):
    setting = ADDON.getSetting(key)
    return _processSetting(setting, default)


def _processSetting(setting, default):
    if not setting:
        return default
    if isinstance(default, bool):
        return setting.lower() == 'true'
    elif isinstance(default, float):
        return float(setting)
    elif isinstance(default, int):
        return int(float(setting or 0))
    elif isinstance(default, list):
        if setting:
            return json.loads(binascii.unhexlify(setting))
        else:
            return default

    return setting


def setSetting(key, value):
    value = _processSettingForWrite(value)
    ADDON.setSetting(key, value)


def _processSettingForWrite(value):
    if isinstance(value, list):
        value = binascii.hexlify(json.dumps(value))
    elif isinstance(value, bool):
        value = value and 'true' or 'false'
    return str(value)


def setGlobalProperty(key, val):
    xbmcgui.Window(10000).setProperty('script.cinemavision.{0}'.format(key), val)


def getGlobalProperty(key):
    return xbmc.getInfoLabel('Window(10000).Property(script.cinemavision.{0})'.format(key))


try:
    xbmc.Monitor().waitForAbort

    def wait(timeout):
        return xbmc.Monitor().waitForAbort(timeout)
except:
    def wait(timeout):
        start = time.time()
        while not xbmc.abortRequested and time.time() - start < timeout:
            xbmc.sleep(100)
        return xbmc.abortRequested


class Progress(object):
    def __init__(self, heading, line1='', line2='', line3=''):
        self.dialog = xbmcgui.DialogProgress()
        self.heading = heading
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        self.pct = 0

    def __enter__(self):
        self.dialog.create(self.heading, self.line1, self.line2, self.line3)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dialog.close()

    def update(self, pct, line1=None, line2=None, line3=None):
        self.pct = pct
        if line1 is not None:
            self.line1 = line1
        if line2 is not None:
            self.line2 = line2
        if line3 is not None:
            self.line3 = line3

        self.dialog.update(self.pct, self.line1, self.line2, self.line3)

    def msg(self, msg=None, heading=None):
        self.update(self.pct, heading, None, msg)

    def iscanceled(self):
        return self.dialog.iscanceled()
