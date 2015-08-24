import os

import xbmcgui
import xbmcvfs

import kodiutil
import kodigui

from lib import cinemavision

API_LEVEL = 1


class ItemSettingsWindow(kodigui.BaseDialog):
    xmlFile = 'script.cinemavision-sequence-item-settings.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    SETTINGS_LIST_ID = 300
    SLIDER_ID = 401

    def __init__(self, *args, **kwargs):
        kodigui.BaseDialog.__init__(self, *args, **kwargs)
        self.main = kwargs['main']
        self.item = kwargs['item']
        self.pos = self.item.pos()
        seqSize = self.main.sequenceControl.size() - 1
        self.leftOffset = int((self.pos + 1) / 2) - 1
        self.rightOffset = int((seqSize - (self.pos + 1)) / 2)
        self.modified = False

    def onFirstInit(self):
        self.settingsList = kodigui.ManagedControlList(self, self.SETTINGS_LIST_ID, 10)
        self.sliderControl = self.getControl(self.SLIDER_ID)
        self.fillSettingsList()
        self.updateItem()

    def fillSettingsList(self, update=False):
        sItem = self.item.dataSource

        items = []
        for i, e in enumerate(sItem._elements):
            if not sItem.elementVisible(e):
                continue
            attr = e['attr']
            mli = kodigui.ManagedListItem(e['name'], unicode(sItem.getSettingDisplay(attr)), data_source=attr)
            if sItem.getType(attr) == int:
                mli.setProperty('type', 'integer')
            items.append(mli)

        if update:
            self.settingsList.replaceItems(items)
        else:
            self.settingsList.reset()
            self.settingsList.addItems(items)

        self.setFocusId(self.SETTINGS_LIST_ID)

    def onAction(self, action):
        try:
            # print action.getId()
            if action == xbmcgui.ACTION_MOVE_LEFT:
                self.moveLeft()
            elif action == xbmcgui.ACTION_MOVE_RIGHT:
                self.moveRight()
            elif action == xbmcgui.ACTION_MOUSE_DRAG:
                self.dragSlider()
            else:
                self.updateItem()

        except:
            kodiutil.ERROR()
            kodigui.BaseDialog.onAction(self, action)
            return

        kodigui.BaseDialog.onAction(self, action)

    def onClick(self, controlID):
        if not controlID == self.SETTINGS_LIST_ID:
            return

        self.editItemSetting()

    def dragSlider(self):
        item = self.settingsList.getSelectedItem()
        if not item or not item.getProperty('type') == 'integer':
            return

        pct = self.sliderControl.getPercent()

        sItem = self.item.dataSource
        attr = item.dataSource
        limits = self.getLimits(sItem, attr)
        total = limits[1] - limits[0]
        val = int(round(((pct/100.0) * total) + limits[0]))
        val = val - (val % limits[2])
        sItem.setSetting(attr, val)

        item.setLabel2(sItem.getSettingDisplay(attr))

        self.modified = True

        self.main.updateSpecials()
        self.main.updateItemSettings(sItem, self.item)

    def updateItem(self):
        item = self.settingsList.getSelectedItem()
        if not item or not item.getProperty('type') == 'integer':
            return

        sItem = self.item.dataSource
        attr = item.dataSource
        if item.getProperty('type') == 'integer':
            val = sItem.getSetting(attr)
            self.updateSlider(val, *self.getLimits(sItem, attr))

        self.main.updateItemSettings(sItem, self.item)

    def moveLeft(self):
        self.moveLR(-1)

    def moveRight(self):
        self.moveLR(1)

    def moveLR(self, offset):
        item = self.settingsList.getSelectedItem()
        if not item or not item.getProperty('type') == 'integer':
            return

        sItem = self.item.dataSource
        attr = item.dataSource
        val = sItem.getSetting(attr)
        limits = self.getLimits(sItem, attr)

        val += offset * limits[2]

        if not limits[0] <= val <= limits[1]:
            return

        sItem.setSetting(attr, val)
        self.updateSlider(val, *limits)
        item.setLabel2(sItem.getSettingDisplay(attr))

        self.modified = True

        self.main.updateSpecials()
        self.main.updateItemSettings(sItem, self.item)

    def updateSlider(self, val, min_val, max_val, step):
        total = max_val - min_val
        val = val - min_val
        pct = (val/float(total)) * 100
        self.sliderControl.setPercent(pct)

    def getLimits(self, sItem, attr):
        limits = sItem.getLimits(attr)
        if sItem._type == 'command':
            if sItem.command == 'back':
                return (limits[0], min(limits[1], self.leftOffset))
            elif sItem.command == 'skip':
                return (limits[0], min(limits[1], self.rightOffset))

        return limits

    def editItemSetting(self):
        self._editItemSetting()
        self.fillSettingsList(update=True)

    def _editItemSetting(self):
        item = self.settingsList.getSelectedItem()
        if not item or item.getProperty('type') == 'integer':
            return

        sItem = self.item.dataSource

        attr = item.dataSource

        options = sItem.getSettingOptions(attr)

        if options == cinemavision.sequence.LIMIT_FILE:
            value = xbmcgui.Dialog().browse(1, 'Select File', 'files', None, False, False, sItem.getSetting(attr))
            if not value:
                return
            value = value.decode('utf-8')
        elif options == cinemavision.sequence.LIMIT_DB_CHOICE:
            options = sItem.DBChoices(attr)
            idx = xbmcgui.Dialog().select('Option', [x[1] for x in options])
            if idx < 0:
                return False
            value = options[idx][0]
        elif options == cinemavision.sequence.LIMIT_DIR:
            value = xbmcgui.Dialog().browse(0, 'Select Directory', 'files')
            if not value:
                return
            value = value.decode('utf-8')
        elif options == cinemavision.sequence.LIMIT_BOOL_DEFAULT:
            curr = sItem.getSetting(attr)
            if curr is None:
                value = True
            elif curr is True:
                value = False
            else:
                value = None
        elif options == cinemavision.sequence.LIMIT_BOOL:
            value = not sItem.getSetting(attr)
        elif isinstance(options, list):
            idx = xbmcgui.Dialog().select('Option', [x[1] for x in options])
            if idx < 0:
                return False
            value = options[idx][0]
        else:
            return False

        sItem.setSetting(attr, value)
        item.setLabel2(unicode(sItem.getSettingDisplay(attr)))

        self.modified = True

        self.main.updateItemSettings(sItem, self.item)

        if sItem._type == 'command' and attr == 'command':
            self.main.updateSpecials()


class SequenceEditorWindow(kodigui.BaseWindow):
    xmlFile = 'script.cinemavision-sequence-editor.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    SEQUENCE_LIST_ID = 201
    ADD_ITEM_LIST_ID = 202
    ITEM_OPTIONS_LIST_ID = 203

    def __init__(self, *args, **kwargs):
        kodigui.BaseWindow.__init__(self, *args, **kwargs)
        self.move = None
        self.modified = False
        self.name = ''
        self.path = ''
        self.content = None

    def onFirstInit(self):
        self.sequenceControl = kodigui.ManagedControlList(self, self.SEQUENCE_LIST_ID, 22)
        self.addItemControl = kodigui.ManagedControlList(self, self.ADD_ITEM_LIST_ID, 22)
        self.itemOptionsControl = kodigui.ManagedControlList(self, self.ITEM_OPTIONS_LIST_ID, 22)
        self.start()

    def onClick(self, controlID):
        if self.focusedOnItem():
            self.itemOptions()
        else:
            self.addItem()
            self.updateFocus(pre=True)

    def onAction(self, action):
        try:
            if action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
                if self.handleClose():
                    return

            if self.move:
                if action == xbmcgui.ACTION_MOVE_LEFT:
                    pos2 = self.sequenceControl.getSelectedPosition()
                    pos1 = pos2 - 2
                    if self.sequenceControl.swapItems(pos1, pos2):
                        self.sequenceControl.selectItem(pos1)
                    self.updateSpecials()
                    return
                elif action == xbmcgui.ACTION_MOVE_RIGHT:
                    pos1 = self.sequenceControl.getSelectedPosition()
                    pos2 = pos1 + 2
                    if self.sequenceControl.swapItems(pos1, pos2):
                        self.sequenceControl.selectItem(pos2)
                    self.updateSpecials()
                    return
            else:
                if action == xbmcgui.ACTION_MOVE_LEFT:
                    pos = self.sequenceControl.getSelectedPosition()
                    pos -= 1
                    if not self.sequenceControl.positionIsValid(pos):
                        pos = self.sequenceControl.size() - 1
                    self.sequenceControl.selectItem(pos)
                    self.updateFocus(pre=True)
                elif action == xbmcgui.ACTION_MOVE_RIGHT:
                    pos = self.sequenceControl.getSelectedPosition()
                    pos += 1
                    if not self.sequenceControl.positionIsValid(pos):
                        pos = 0
                    self.sequenceControl.selectItem(pos)
                    self.updateFocus(pre=True)
                elif action == xbmcgui.ACTION_CONTEXT_MENU:
                        self.doMenu()

        except:
            kodiutil.ERROR()

        kodigui.BaseWindow.onAction(self, action)

    def handleClose(self):
        yes = True
        if self.modified:
            yes = xbmcgui.Dialog().yesno('Confirm', 'Sequence was modified.', '', 'Do you really want to exit without saving changes?')

        if yes:
            return False

        self.save(as_new=True)

        return True

    def updateFocus(self, pre=False):
        if (pre and not self.focusedOnItem()) or (not pre and self.focusedOnItem()):
            self.setFocusId(self.ITEM_OPTIONS_LIST_ID)
        else:
            self.setFocusId(self.ADD_ITEM_LIST_ID)

    def start(self):
        self.loadContent()
        self.fillOptions()
        self.fillSequence()
        self.loadDefault()

    def loadContent(self):
        contentPath = kodiutil.getSetting('content.path')
        if not contentPath:
            return
        kodiutil.DEBUG_LOG('Loading content...')

        with kodiutil.Progress('Loading Content') as p:
            self.content = cinemavision.content.UserContent(contentPath, callback=p.msg)

    def fillOptions(self):
        for i in cinemavision.sequence.ITEM_TYPES:
            item = kodigui.ManagedListItem('Add {0}'.format(i[1]), thumbnailImage='small/script.cinemavision-{0}.png'.format(i[2]), data_source=i[0])
            item.setProperty('thumb.focus', 'small/script.cinemavision-{0}_selected.png'.format(i[2]))
            self.addItemControl.addItem(item)

        item = kodigui.ManagedListItem('Disable', 'Enable', thumbnailImage='small/script.cinemavision-disable.png', data_source='enable')
        item.setProperty('alt.thumb', 'small/script.cinemavision-enable.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Copy', 'Copy', thumbnailImage='small/script.cinemavision-copy.png', data_source='copy')
        item.setProperty('alt.thumb', 'small/script.cinemavision-copy.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Move', 'Move', thumbnailImage='small/script.cinemavision-move.png', data_source='move')
        item.setProperty('alt.thumb', 'small/script.cinemavision-move.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Edit', 'Edit', thumbnailImage='small/script.cinemavision-edit.png', data_source='edit')
        item.setProperty('alt.thumb', 'small/script.cinemavision-edit.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Rename', 'Rename', thumbnailImage='small/script.cinemavision-rename.png', data_source='rename')
        item.setProperty('alt.thumb', 'small/script.cinemavision-rename.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Remove', 'Remove', thumbnailImage='small/script.cinemavision-minus.png', data_source='remove')
        item.setProperty('alt.thumb', 'small/script.cinemavision-minus.png')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)

    def fillSequence(self):
        mli = kodigui.ManagedListItem()

        self.sequenceControl.addItem(mli)
        # self.setFocusId(self.SEQUENCE_LIST_ID)

    def addItem(self):
        item = self.addItemControl.getSelectedItem()
        if not item:
            return

        pos = self.sequenceControl.getSelectedPosition()

        sItem = cinemavision.sequence.getItem(item.dataSource)()

        self.insertItem(sItem, pos)

    def insertItem(self, sItem, pos):
        mli = kodigui.ManagedListItem(sItem.display(), data_source=sItem)
        mli.setProperty('type', sItem.fileChar)
        mli.setProperty('type.name', sItem.displayName)
        mli.setProperty('enabled', sItem.enabled and '1' or '')

        self.updateItemSettings(sItem, mli)

        self.sequenceControl.insertItem(pos, mli)
        self.sequenceControl.insertItem(pos, kodigui.ManagedListItem())

        self.updateFirstLast()

        self.modified = True
        self.updateSpecials()

    def addItems(self, items):
        final = []
        for sItem in items:
            mli = kodigui.ManagedListItem(sItem.display(), data_source=sItem)
            mli.setProperty('type', sItem.fileChar)
            mli.setProperty('type.name', sItem.displayName)
            mli.setProperty('enabled', sItem.enabled and '1' or '')

            self.updateItemSettings(sItem, mli)

            final.append(mli)
            final.append(kodigui.ManagedListItem())

        self.sequenceControl.addItems(final)

        self.updateFirstLast()

        self.modified = True
        self.updateSpecials()

    def updateFirstLast(self):
        for i in self.sequenceControl:
            i.setProperty('first', '')
            i.setProperty('last', '')
            i.setProperty('second', '')
            i.setProperty('almost.last', '')
        self.sequenceControl[0].setProperty('first', '1')
        self.sequenceControl[self.sequenceControl.size() - 1].setProperty('last', '1')
        if self.sequenceControl.size() > 1:
            self.sequenceControl[1].setProperty('second', '1')
            self.sequenceControl[self.sequenceControl.size() - 2].setProperty('almost.last', '1')

    def updateSpecials(self):
        skip = 0
        for i in self.sequenceControl:
            sItem = i.dataSource

            i.setProperty('connect.start', '')
            i.setProperty('connect.join', '')
            i.setProperty('connect.end', '')
            i.setProperty('connect.skip.start', '')
            i.setProperty('connect.skip.join', '')
            i.setProperty('connect.skip.end', '')

            if not sItem:
                continue

            i.setLabel(sItem.display())

            if sItem.enabled and sItem._type == 'command':
                if sItem.command == 'back':
                    pos = i.pos()
                    all = range(1, (sItem.arg * 2) + 1)
                    last = pos - all[-1]

                    i.setProperty('connect.end', '1')
                    prev = None

                    for x in all:
                        modPos = pos - x
                        if modPos < 0:
                            break
                        item = self.sequenceControl[modPos]
                        if not item.dataSource:
                            continue

                        if item.dataSource._type == 'command' and item.dataSource.command == 'back':
                            if prev:
                                prev.setProperty('connect.start', '1')
                                prev.setProperty('connect.join', '')
                            break

                        if modPos == 1 or modPos == last:
                            item.setProperty('connect.start', '1')
                        else:
                            item.setProperty('connect.join', '1')

                        prev = item
                elif sItem.command == 'skip':
                    skip = sItem.arg
                    i.setProperty('connect.skip.start', '1')

            if skip:
                if not i.getProperty('connect.skip.start'):
                    skip -= 1
                    if skip == 0:
                        i.setProperty('connect.skip.end', '1')
                    else:
                        i.setProperty('connect.skip.join', '1')

    def itemOptions(self):
        if self.move:
            return self.moveItem()
        item = self.itemOptionsControl.getSelectedItem()
        if not item:
            return

        if item.dataSource == 'enable':
            self.toggleItemEnabled()
        elif item.dataSource == 'remove':
            self.removeItem()
            self.updateFocus()
        elif item.dataSource == 'copy':
            self.copyItem()
            self.updateFocus()
        elif item.dataSource == 'move':
            self.moveItem()
        elif item.dataSource == 'edit':
            self.editItem()
            self.updateFocus()
        elif item.dataSource == 'rename':
            self.renameItem()

        self.updateSpecials()

    def toggleItemEnabled(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return

        sItem = item.dataSource
        sItem.enabled = not sItem.enabled
        item.setProperty('enabled', sItem.enabled and '1' or '')
        self.updateItemSettings(sItem, item)

        self.modified = True

    def removeItem(self):
        if not xbmcgui.Dialog().yesno('Confirm', '', 'Do you really want to remove this module?'):
            return

        pos = self.sequenceControl.getSelectedPosition()
        if pos < 0:
            return
        self.sequenceControl.removeItem(pos)
        self.sequenceControl.removeItem(pos)

        self.updateFirstLast()

        self.modified = True

    def copyItem(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return

        sItem = item.dataSource.copy()

        self.insertItem(sItem, item.pos() + 1)

    def moveItem(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return
        if self.move:
            kodiutil.DEBUG_LOG('Move item: Finished')
            self.move.setProperty('moving', '')
            self.move = None
            self.modified = True
        else:
            kodiutil.DEBUG_LOG('Move item: Started')
            self.move = item
            self.move.setProperty('moving', '1')

    def editItem(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return
        isw = ItemSettingsWindow.open(main=self, item=item)

        sItem = item.dataSource

        self.updateItemSettings(sItem, item)
        if not self.modified:
            self.modified = isw.modified

    def updateItemSettings(self, sItem, item):
        ct = 0
        item.setProperty('setting{0}'.format(ct), sItem.enabled and 'Yes' or 'No')
        item.setProperty('setting{0}_name'.format(ct), 'Enabled')
        ct += 1
        for e in sItem._elements:
            if not sItem.elementVisible(e):
                continue
            disp = sItem.getSettingDisplay(e['attr'])
            item.setProperty('setting{0}'.format(ct), disp)
            item.setProperty('setting{0}_name'.format(ct), e['name'])
            ct += 1
        for i in range(ct, 8):
            item.setProperty('setting{0}'.format(i), '')
            item.setProperty('setting{0}_name'.format(i), '')

    def renameItem(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return

        sItem = item.dataSource

        name = xbmcgui.Dialog().input('Enter a name for this item', sItem.name)

        if name == sItem.name:
            return

        sItem.name = name or ''

        self.modified = True

    def focusedOnItem(self):
        item = self.sequenceControl.getSelectedItem()
        return bool(item.dataSource)

    def doMenu(self):
        options = []
        options.append(('new', 'New Sequence'))
        options.append(('save', 'Save Sequence'))
        options.append(('saveas', 'Save Sequence As...'))
        options.append(('load', 'Load Sequence...'))
        options.append(('test', 'Play Sequence'))
        idx = xbmcgui.Dialog().select('Options', [o[1] for o in options])
        if idx < 0:
            return
        option = options[idx][0]

        if option == 'new':
            self.new()
        elif option == 'save':
            self.save()
        elif option == 'saveas':
            self.save(as_new=True)
        elif option == 'load':
            self.load()
        elif option == 'test':
            self.test()

    def test(self):
        import experience
        savePath = self.savePath()
        if not savePath:
            savePath = self.defaultSavePath()

        e = experience.ExperiencePlayer().create()
        e.start(savePath)

    def new(self):
        if self.modified:
            if not xbmcgui.Dialog().yesno('Confirm', 'Sequence is modified.', 'This will delete all changes.', 'Do you really want to do this?'):
                return
        self.name = ''
        self.sequenceControl.reset()
        self.fillSequence()

    def savePath(self, path=None, name=None):
        path = path or self.path
        name = name or self.name
        if not name or not path:
            return None

        return cinemavision.util.pathJoin(path, name) + '.cvseq'

    def defaultSavePath(self):
        path = os.path.join(kodiutil.ADDON_PATH, 'resources')
        return self.savePath(path, 'script.cinemavision.default')

    def save(self, as_new=False):
        items = [li.dataSource for li in self.sequenceControl if li.dataSource]
        xmlString = cinemavision.sequence.getSaveString(items)

        if not self.path or as_new:
            path = xbmcgui.Dialog().browse(3, 'Select Save Directory', 'files', None, False, False, self.path)
            print path
            if not path:
                return
            self.path = path

        if not self.name or as_new:
            as_new = True  # Because we set name, we want to at least check the path
            name = xbmcgui.Dialog().input('Enter Name For File', self.name)
            if not name:
                return
            self.name = name

        fullPath = self.savePath()

        kodiutil.DEBUG_LOG('Saving to: {0}'.format(fullPath))

        f = xbmcvfs.File(fullPath, 'w')
        f.write(xmlString)
        f.close()

        self.modified = False

        # print xmlString
        # test = cinemavision.sequence.getItemsFromString(xmlString)
        # print test
        self.saveDefault()

    def load(self, path=None):
        path = path or xbmcgui.Dialog().browse(1, 'Select File', 'files', '*.cvseq', False, False, self.path)
        if not path or path == self.path:
            return

        self._load(path)

        sep = cinemavision.util.getSep(path)

        self.path, name = path.rsplit(sep, 1)
        self.path += sep
        self.name = name.rsplit('.', 1)[0]

        self.saveDefault()

    def _load(self, path):
        f = xbmcvfs.File(path, 'r')
        xmlString = f.read().decode('utf-8')
        f.close()
        sItems = cinemavision.sequence.getItemsFromString(xmlString)
        self.sequenceControl.reset()
        self.fillSequence()

        self.addItems(sItems)

        if self.sequenceControl.positionIsValid(1):
            self.sequenceControl.selectItem(1)
            self.setFocusId(self.ITEM_OPTIONS_LIST_ID)
        else:
            self.setFocusId(self.ADD_ITEM_LIST_ID)

        self.modified = False

    def saveDefault(self, force=True):
        if (not self.name or not self.path) and not force:
            return
        kodiutil.setSetting('save.name', self.name)
        kodiutil.setSetting('save.path', self.path)

    def loadDefault(self):
        self.name = kodiutil.getSetting('save.name', '')
        self.path = kodiutil.getSetting('save.path', '')

        if not self.name and not self.path:
            savePath = self.defaultSavePath()
        else:
            savePath = self.savePath()
            if not xbmcvfs.exists(savePath):
                self.path = ''
                self.name = ''
                self.saveDefault(force=True)
                new = xbmcgui.Dialog().yesno('Missing', 'Previous save not found.', '', 'Load the default or start a new sequence?', 'Default', 'New')
                if new:
                    self.name = ''
                    if not xbmcvfs.exists(self.path):
                        self.path = ''
                    self.setFocusId(self.ADD_ITEM_LIST_ID)
                    return
                else:
                    savePath = self.defaultSavePath()

        kodiutil.DEBUG_LOG('Loading previous save: {0}'.format(savePath))

        self._load(savePath)

        kodiutil.DEBUG_LOG('Previous save loaded')


def firstRun():
    kodiutil.LOG('FIRST RUN')


def checkAPILevel():
    old = kodiutil.getSetting('API_LEVEL', 0)
    if not old:
        firstRun()
    kodiutil.setSetting('API_LEVEL', API_LEVEL)


def main():
    checkAPILevel()
    kodiutil.LOG('Sequence editor: OPENING')
    SequenceEditorWindow.open()
    kodiutil.LOG('Sequence editor: CLOSED')
