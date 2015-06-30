import kodiutil
import kodigui


ITEM_TYPES = [
    ('A', 'Action'),
    ('C', 'Command'),
    ('F', 'Feature'),
    ('Q', 'Trivia'),
    ('R', 'Rating'),
    ('S', 'Cinema Spot'),
    ('T', 'Trailer')
]


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

    def onFirstInit(self):
        self.sequenceControl = kodigui.ManagedControlList(self, self.SEQUENCE_LIST_ID, 22)
        self.addItemControl = kodigui.ManagedControlList(self, self.ADD_ITEM_LIST_ID, 22)
        self.itemOptionsControl = kodigui.ManagedControlList(self, self.ITEM_OPTIONS_LIST_ID, 22)
        self.start()

    def start(self):
        self.fillOptions()
        self.fillSequence()

    def fillOptions(self):
        for i in ITEM_TYPES:
            item = kodigui.ManagedListItem('Add {0}'.format(i[1]), thumbnailImage='script.cinemavision-{0}.png'.format(i[0]))
            item.setProperty('thumb.focus', 'script.cinemavision-{0}_selected.png'.format(i[0]))
            self.addItemControl.addItem(item)

        item = kodigui.ManagedListItem('Remove', thumbnailImage='script.cinemavision-minus.png')
        item.setProperty('thumb.focus', 'script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Move', thumbnailImage='script.cinemavision-move.png')
        item.setProperty('thumb.focus', 'script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)
        item = kodigui.ManagedListItem('Edit', thumbnailImage='script.cinemavision-edit.png')
        item.setProperty('thumb.focus', 'script.cinemavision-A_selected.png')
        self.itemOptionsControl.addItem(item)

    def fillSequence(self):
        items = []
        for i in (
            None, ('Q', ''), None, ('A', ''), None, ('S', ''), None, ('T', ''), None, ('R', ''), None, ('S', ''), None, ('Q', 'start'), None,
            ('T', 'join'), None, ('R', 'join'), None, ('F', 'join'), None, ('C', 'end'), None, ('S', ''), None, ('Q', ''),
            None, ('T', ''), None, ('R', ''), None
        ):
            label = i and next((x for x in ITEM_TYPES if x[0] == i[0]), ('', ''))[1] or ''

            mli = kodigui.ManagedListItem(label)
            if i and i[0] == 'A':
                mli.setLabel2('(Lights: 0%, 4s)')
            if i and i[0] == 'C':
                mli.setLabel2('(Back: 4)')
            if i and i[1]:
                mli.setProperty('connect.{0}'.format(i[1]), '1')

            mli.setProperty('type', i and i[0] or '')

            items.append(mli)
        items[0].setProperty('first', '1')
        items[-1].setProperty('last', '1')
        self.sequenceControl.addItems(items)
        self.setFocusId(self.SEQUENCE_LIST_ID)


def main():
    kodiutil.LOG('Sequence editor: OPENING')
    SequenceEditorWindow.open()
    kodiutil.LOG('Sequence editor: CLOSED')
