def clearDBWatchedStatus():
    from cinemavision import database as DB

    DB.WatchedTrailers.update(watched=False).where(
        DB.WatchedTrailers.watched == 1
    ).execute()

    import xbmcgui
    xbmcgui.Dialog().ok('Done', 'Remove watched status from all trailers.')


def pasteLog():
    import os
    import re
    import xbmc
    import xbmcgui
    import kodiutil
    from pastebin_python import PastebinPython

    def debug_log(msg):
        kodiutil.DEBUG_LOG('PASTEBIN: {0}'.format(msg))

    replaces = (
        ('//.+?:.+?@', '//USER:PASSWORD@'),
        ('<user>.+?</user>', '<user>USER</user>'),
        ('<pass>.+?</pass>', '<pass>PASSWORD</pass>'),
    )

    apiUserKey = kodiutil.getSetting('pastebin.user.key')

    pb = PastebinPython(api_dev_key=kodiutil.getPeanutButter(), api_user_key=apiUserKey)

    apiUser = kodiutil.getSetting('pastebin.user')
    if apiUser and not apiUserKey:
        debug_log('Username set, asking user for password')
        password = xbmcgui.Dialog().input('Enter Pastebin password (only needed 1st time - NOT stored)')
        if password:
            debug_log('Getting API user key')
            apiUserKey = pb.createAPIUserKey(apiUser, password)
            if apiUserKey.lower().startswith('bad'):
                xbmcgui.Dialog().ok('Failed', u'Failed to create paste as user: {0}'.format(apiUser), '', apiUserKey)
                debug_log('Failed get user API key ({0}): {1}'.format(apiUser, apiUserKey))
            else:
                kodiutil.setSetting('pastebin.user.key', apiUserKey)
        else:
            debug_log('User aborted')
            xbmcgui.Dialog().ok('Aborted', ' ', 'Paste aborted!')
            return

    elif apiUserKey:
        debug_log('Creating paste with stored API key')

    logPath = os.path.join(xbmc.translatePath('special://logpath').decode('utf-8'), 'kodi.log')
    with kodiutil.Progress('Pastebin', 'Creating paste...'):
        with open(logPath, 'r') as f:
            content = f.read().decode('utf-8')
            for pattern, repl in replaces:
                content = re.sub(pattern, repl, content)
            urlOrError = pb.createPaste(content, 'Kodi CV LOG', api_paste_private=1, api_paste_expire_date='1W')

    showQR = False
    if urlOrError.startswith('http'):
        showQR = xbmcgui.Dialog().yesno('Done', 'Paste created at:', '', urlOrError, 'OK', 'Show QR Code')
        debug_log('Paste created: {0}'.format(urlOrError))
    else:
        xbmcgui.Dialog().ok('Failed', 'Failed to create paste:', '', urlOrError)
        debug_log('Failed to create paste: {0}'.format(urlOrError))

    if showQR:
        showQRCode(urlOrError)


def showQRCode(url):
    import os
    import pyqrcode
    import kodiutil
    from kodijsonrpc import rpc

    with kodiutil.Progress('QR Code', 'Creating QR code...'):
        code = pyqrcode.create(url)
        QRDir = os.path.join(kodiutil.PROFILE_PATH, 'settings', 'QR')
        if not os.path.exists(QRDir):
            os.makedirs(QRDir)
        QR = os.path.join(QRDir, 'QR.png')
        code.png(QR, scale=6)
    rpc.Player.Open(item={'path': QRDir})
