import experience
import kodiutil
import cvutil
import kodigui
import xbmc
import xbmcgui


def showNoFeaturesDialog():
    import xbmcgui
    xbmcgui.Dialog().ok('No Features', 'No movies are in the Queue.', '', 'Please queue some features and try again.')


def featureComfirmationDialog(features):
    pd = PlaylistDialog.open(features=features)
    if not pd.play:
        return None

    return pd.features


def begin():
    e = experience.ExperiencePlayer().create()

    if not e.hasFeatures():
        if not e.addSelectedFeature():
            return showNoFeaturesDialog()

    if not kodiutil.getSetting('hide.queue.dialog', False) or (kodiutil.getSetting('hide.queue.dialog.single', False) and len(e.features) > 1):
        e.features = featureComfirmationDialog(e.features)

    if not e.features:
        return

    seqPath = cvutil.getSequencePath(for_3D=e.has3D)

    kodiutil.DEBUG_LOG('Loading sequence for {0}: {1}'.format(e.has3D and '3D' or '2D', repr(seqPath)))

    e.start(seqPath)


class PlaylistDialog(kodigui.BaseDialog):
    xmlFile = 'script.cinemavision-playlist-dialog.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    VIDEOS_LIST_ID = 300
    PLAY_BUTTON_ID = 201
    CANCEL_BUTTON_ID = 202

    def __init__(self, *args, **kwargs):
        kodigui.BaseDialog.__init__(self, *args, **kwargs)
        self.features = kwargs.get('features', [])
        self.play = False
        self.moving = None

    def onFirstInit(self):
        self.videoListControl = kodigui.ManagedControlList(self, self.VIDEOS_LIST_ID, 5)
        self.start()

    def onClick(self, controlID):
        if controlID == self.PLAY_BUTTON_ID:
            self.play = True
            self.doClose()
        elif controlID == self.CANCEL_BUTTON_ID:
            self.doClose()
        elif controlID == self.VIDEOS_LIST_ID:
            self.moveItem()

    def onAction(self, action):
        try:
            if action == xbmcgui.ACTION_CONTEXT_MENU:
                self.delete()
                return
            elif action in (
                xbmcgui.ACTION_MOVE_UP,
                xbmcgui.ACTION_MOVE_DOWN,
                xbmcgui.ACTION_MOUSE_MOVE,
                xbmcgui.ACTION_MOUSE_WHEEL_UP,
                xbmcgui.ACTION_MOUSE_WHEEL_DOWN
            ):
                if self.getFocusId() == self.VIDEOS_LIST_ID:
                    self.moveItem(True)
                return
            elif action.getButtonCode() in (61575, 61486):
                self.delete()
        except:
            kodigui.BaseDialog.onAction(self, action)
            kodiutil.ERROR()
            return

        kodigui.BaseDialog.onAction(self, action)

    def start(self):
        items = []
        for f in self.features:
            mli = kodigui.ManagedListItem(f.title, f.durationMinutesDisplay, thumbnailImage=f.thumb, data_source=f)
            mli.setProperty('rating', str(f.rating or ''))
            items.append(mli)

        self.videoListControl.addItems(items)
        xbmc.sleep(100)
        self.setFocusId(self.PLAY_BUTTON_ID)

    def delete(self):
        item = self.videoListControl.getSelectedItem()
        if not item:
            return

        # yes = xbmcgui.Dialog().yesno('Remove', '', 'Remove?')
        yes = True
        if yes:
            self.videoListControl.removeItem(item.pos())
            self.updateReturn()

    def updateReturn(self):
        self.features = [i.dataSource for i in self.videoListControl]
        if not self.features:
            self.setFocusId(self.CANCEL_BUTTON_ID)

    def moveItem(self, move=False):
        if move:
            if self.moving:
                pos = self.videoListControl.getSelectedPosition()
                self.videoListControl.moveItem(self.moving, pos)
        else:
            if self.moving:
                self.moving.setProperty('moving', '')
                self.moving = None
                self.updateReturn()
            else:
                item = self.videoListControl.getSelectedItem()
                self.moving = item
                item.setProperty('moving', '1')
