import xbmcgui

import kodiutil
import kodigui

from lib import cinemavision


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

    def onAction(self, action):
        try:
            if self.move:
                if action == xbmcgui.ACTION_MOVE_LEFT:
                    pos2 = self.sequenceControl.getSelectedPosition()
                    pos1 = pos2 - 2
                    if self.sequenceControl.swapItems(pos1, pos2):
                        self.sequenceControl.selectItem(pos1)
                    return
                elif action == xbmcgui.ACTION_MOVE_RIGHT:
                    pos1 = self.sequenceControl.getSelectedPosition()
                    pos2 = pos1 + 2
                    if self.sequenceControl.swapItems(pos1, pos2):
                        self.sequenceControl.selectItem(pos2)
                    return
            else:
                if action == xbmcgui.ACTION_MOVE_LEFT:
                    pos = self.sequenceControl.getSelectedPosition()
                    pos -= 1
                    if self.sequenceControl.positionIsValid(pos):
                        self.sequenceControl.selectItem(pos)
                    return
                elif action == xbmcgui.ACTION_MOVE_RIGHT:
                    pos = self.sequenceControl.getSelectedPosition()
                    pos += 1
                    if self.sequenceControl.positionIsValid(pos):
                        self.sequenceControl.selectItem(pos)
                    return

                if self.focusedOnItem():
                    self.setFocusId(self.ITEM_OPTIONS_LIST_ID)
                else:
                    self.setFocusId(self.ADD_ITEM_LIST_ID)

                if action == xbmcgui.ACTION_CONTEXT_MENU:
                        self.doMenu()

        except:
            kodiutil.ERROR()

        kodigui.BaseWindow.onAction(self, action)

    def start(self):
        self.fillOptions()
        self.fillSequence()

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
        pass
        # items = []
        # command = ['(Lights: 0%, 4s)', '(Lights: 100%, 4s)']
        # for i in (
        #     None, ('Q', ''), None, ('_', ''), None, ('V', ''), None, ('T', ''), None, ('V', ''), None, ('Q', 'start'), None,
        #     ('T', 'join'), None, ('A', 'join'), None, ('F', 'join'), None, ('C', 'end'), None, ('V', ''), None, ('Q', ''),
        #     None, ('T', ''), None, ('_', ''), None
        # ):
        #     label = i and next((x for x in ITEM_TYPES if x[0] == i[0]), ('', ''))[1] or ''
        #     mli = kodigui.ManagedListItem(label)
        #     if i and i[0] == '_':
        #         mli.setLabel2(command.pop(0))
        #     if i and i[0] == 'C':
        #         mli.setLabel2('(Back: 4)')
        #     if i and i[1]:
        #         mli.setProperty('connect.{0}'.format(i[1]), '1')

        #     mli.setProperty('type', i and i[0] or '')

        #     items.append(mli)
        # items[0].setProperty('first', '1')
        # items[-1].setProperty('last', '1')
        mli = kodigui.ManagedListItem('')

        self.sequenceControl.addItem(mli)
        self.setFocusId(self.SEQUENCE_LIST_ID)

    def addItem(self):
        item = self.addItemControl.getSelectedItem()
        if not item:
            return

        print item.getLabel()

        pos = self.sequenceControl.getSelectedPosition()

        sItem = cinemavision.sequence.getItem(item.dataSource)()

        mli = kodigui.ManagedListItem(sItem.displayName, data_source=sItem)
        mli.setProperty('type', sItem.fileChar)

        self.sequenceControl.insertItem(pos, mli)
        self.sequenceControl.insertItem(pos, kodigui.ManagedListItem())

        self.sequenceControl[0].setProperty('first', '1')
        self.sequenceControl[self.sequenceControl.size() - 1].setProperty('last', '1')
        for i in self.sequenceControl[1:-1]:
            i.setProperty('first', '')
            i.setProperty('last', '')

    def itemOptions(self):
        item = self.itemOptionsControl.getSelectedItem()
        if not item:
            return

        if item.dataSource == 'move':
            self.moveItem()

    def moveItem(self):
        item = self.sequenceControl.getSelectedItem()
        if not item:
            return
        if self.move:
            kodiutil.DEBUG_LOG('Move item: Finished')
            self.move.setProperty('moving', '')
            self.move = None
        else:
            kodiutil.DEBUG_LOG('Move item: Started')
            self.move = item
            self.move.setProperty('moving', '1')

    def focusedOnItem(self):
        item = self.sequenceControl.getSelectedItem()
        return bool(item.dataSource)

    def doMenu(self):
        options = []
        options.append(('save', 'Save'))
        idx = xbmcgui.Dialog().select('Options', [o[1] for o in options])
        if idx < 0:
            return
        option = options[idx][0]

        if option == 'save':
            self.save()

    def save(self):
        items = [li.dataSource for li in self.sequenceControl if li.dataSource]
        xmlString = cinemavision.sequence.getSaveString(items)
        print xmlString
        test = cinemavision.sequence.getItemsFromString(xmlString)
        print test


def main():
    kodiutil.LOG('Sequence editor: OPENING')
    SequenceEditorWindow.open()
    kodiutil.LOG('Sequence editor: CLOSED')
