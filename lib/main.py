import os

import xbmc
import xbmcgui
import xbmcvfs

import kodiutil
import kodigui

from lib import cinemavision

API_LEVEL = 1


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
                    if self.sequenceControl.positionIsValid(pos):
                        self.sequenceControl.selectItem(pos)
                        self.updateFocus(pre=True)
                elif action == xbmcgui.ACTION_MOVE_RIGHT:
                    pos = self.sequenceControl.getSelectedPosition()
                    pos += 1
                    if self.sequenceControl.positionIsValid(pos):
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
            yes = xbmcgui.Dialog().yesno('Confirm', 'Sequence is modified.', '', 'Really exit?')
        return not yes

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
        self.setFocusId(self.ADD_ITEM_LIST_ID)

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

        item = kodigui.ManagedListItem('Remove', thumbnailImage='small/script.cinemavision-minus.png', data_source='remove')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Move', thumbnailImage='small/script.cinemavision-move.png', data_source='move')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Edit', thumbnailImage='small/script.cinemavision-edit.png', data_source='edit')
        item.setProperty('thumb.focus', 'small/script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)

    def fillSequence(self):
        mli = kodigui.ManagedListItem()

        self.sequenceControl.addItem(mli)
        self.setFocusId(self.SEQUENCE_LIST_ID)

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
        ct = 0
        for e in sItem._elements:
            mli.setProperty('setting{0}'.format(ct), str(getattr(sItem, e['attr'])))
            mli.setProperty('setting{0}_name'.format(ct), e['name'])
            ct += 1

        self.sequenceControl.insertItem(pos, mli)
        self.sequenceControl.insertItem(pos, kodigui.ManagedListItem())

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

            if sItem._type == 'command':
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

        if item.dataSource == 'remove':
            self.removeItem()
            self.updateFocus()
        elif item.dataSource == 'move':
            self.moveItem()
        elif item.dataSource == 'edit':
            self.editItem()
            self.updateFocus()

        self.updateSpecials()

    def removeItem(self):
        if not xbmcgui.Dialog().yesno('Confirm', '', 'Do you really want to remove this item?'):
            return

        pos = self.sequenceControl.getSelectedPosition()
        if pos < 0:
            return
        self.sequenceControl.removeItem(pos)
        self.sequenceControl.removeItem(pos)

        self.updateFirstLast()

        self.modified = True

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

        sItem = item.dataSource

        while True:
            options = []

            for e in sItem._elements:
                options.append((e['attr'], e['name']))

            idx = xbmcgui.Dialog().select('Settings', [o[1] for o in options])

            if idx < 0:
                return

            option = options[idx][0]
            self.editItemSetting(item, option)

    def editItemSetting(self, item, attr):
        sItem = item.dataSource
        options = sItem.getSettingOptions(attr)
        if isinstance(options, basestring):
            value = xbmcgui.Dialog().input('Enter Value', str(sItem.getSetting(attr)))
            if value is None:
                return False
        elif isinstance(options, tuple):
            value = int(xbmcgui.Dialog().numeric(0, 'Enter Value', str(sItem.getSetting(attr))))
        elif isinstance(options, list):
            idx = xbmcgui.Dialog().select('Option', options)
            if idx < 0:
                return False
            value = options[idx]
        else:
            return False

        sItem.setSetting(attr, value)
        self.modified = True

        ct = 0
        for e in sItem._elements:
            item.setProperty('setting{0}'.format(ct), str(sItem.getSetting(e['attr'])))
            item.setProperty('setting{0}_name'.format(ct), e['name'])
            ct += 1

        return True

    def focusedOnItem(self):
        item = self.sequenceControl.getSelectedItem()
        return bool(item.dataSource)

    def doMenu(self):
        options = []
        options.append(('new', 'New'))
        options.append(('save', 'Save'))
        options.append(('saveas', 'Save As...'))
        options.append(('load', 'Load...'))
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

    def new(self):
        if self.modified:
            if not xbmcgui.Dialog().yesno('Confirm', 'Sequence is modified.', 'This will delete all changes.', 'Do you really want to do this?'):
                return
        self.name = ''
        self.sequenceControl.reset()
        self.fillSequence()

    def savePath(self, path=None):
        return xbmc.translatePath('{0}{1}.cvseq'.format(path or self.path, self.name))

    def save(self, as_new=False):
        items = [li.dataSource for li in self.sequenceControl if li.dataSource]
        xmlString = cinemavision.sequence.getSaveString(items)

        if not self.name or as_new:
            as_new = True  # Because we set name, we want to at least check the path
            name = xbmcgui.Dialog().input('Enter Name For File', self.name)
            if not name:
                return
            self.name = name

        if not self.path or as_new:
            path = xbmcgui.Dialog().browse(3, 'Select Save Directory', 'files', None, False, False, self.path)
            if not path:
                return
            self.path = path

        fullPath = self.savePath()

        kodiutil.DEBUG_LOG('Saving to: {0}'.format(fullPath))

        f = xbmcvfs.File(fullPath, 'w')
        f.write(xmlString.encode('utf-8'))
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

        f = xbmcvfs.File(path, 'r')
        xmlString = f.read().decode('utf-8')
        f.close()
        sItems = cinemavision.sequence.getItemsFromString(xmlString)
        self.sequenceControl.reset()
        self.fillSequence()
        for sItem in sItems:
            self.insertItem(sItem, -1)

        sep = '/'
        if '\\' in path:
            sep = '\\'
        self.path, name = path.rsplit(sep, 1)
        self.path += sep
        self.name = name.rsplit('.', 1)[0]
        self.modified = False

        self.saveDefault()

        if self.sequenceControl.positionIsValid(1):
            self.sequenceControl.selectItem(1)

    def saveDefault(self):
        if not self.name or not self.path:
            return
        kodiutil.setSetting('save.name', self.name)
        kodiutil.setSetting('save.path', self.path)

    def loadDefault(self):
        self.name = kodiutil.getSetting('save.name', '')

        clearPath = False

        if self.name == 'script.cinemavision.default' and not self.path:
            path = os.path.join(kodiutil.ADDON_PATH, 'resources') + '/'
            savePath = self.savePath(path)
            clearPath = True
        else:
            self.path = kodiutil.getSetting('save.path', '')
            savePath = self.savePath()

            if not self.name or not self.path or not xbmcvfs.exists(savePath):
                self.name = ''
                if not xbmcvfs.exists(self.path):
                    self.path = ''
                return

        kodiutil.DEBUG_LOG('Loading previous save: {0}'.format(savePath))
        self.load(savePath)
        if clearPath:  # Don't want our save directory to be set in the addon path
            self.path = ''
        kodiutil.DEBUG_LOG('Previous save loaded')


def firstRun():
    kodiutil.setSetting('save.name', 'script.cinemavision.default')


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
