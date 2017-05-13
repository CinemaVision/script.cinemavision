import xbmcgui
import kodigui
import kodiutil


class SeqAttrEditorDialog(kodigui.BaseDialog):
    xmlFile = 'script.cinemavision-sequence-attribute-editor.xml'
    path = kodiutil.ADDON_PATH
    theme = 'Main'
    res = '1080i'

    ATTRIBUTE_LIST_ID = 300
    SLIDER_ID = 401

    def __init__(self, *args, **kwargs):
        kodigui.BaseDialog.__init__(self, *args, **kwargs)
        self.sequenceData = kwargs['sequence_data']
        self.modified = False

    def onFirstInit(self):
        self.attributeList = kodigui.ManagedControlList(self, self.ATTRIBUTE_LIST_ID, 10)
        self.sliderControl = self.getControl(self.SLIDER_ID)
        self.fillAttributeList()

    def fillAttributeList(self, update=False):
        self.options = []
        self.options.append(('active', 'Active'))
        self.options.append(('type', 'Type'))
        self.options.append(('year', 'Year(s)'))
        self.options.append(('studios', 'Studio(s)'))
        self.options.append(('directors', 'Director(s)'))
        self.options.append(('genres', 'Genre(s)'))

        items = []
        for o in self.options:
            mli = kodigui.ManagedListItem(data_source=o)
            self.updateItem(mli)
            items.append(mli)

        if update:
            self.attributeList.replaceItems(items)
        else:
            self.attributeList.reset()
            self.attributeList.addItems(items)

        self.setFocusId(self.ATTRIBUTE_LIST_ID)

    def onClick(self, controlID):
        if controlID == self.ATTRIBUTE_LIST_ID:
            self.attributeClicked()

    def attributeClicked(self):
        item = self.attributeList.getSelectedItem()
        if not item:
            return
        option = item.dataSource[0]
        label = item.dataSource[1]

        val = None

        if option in ('year', 'genres', 'studios', 'directors'):
            val = xbmcgui.Dialog().input(u'Enter {0}'.format(label), ','.join([str(v) for v in self.sequenceData.get(option, [])]))
            if option == 'year':
                try:
                    val = [int(v.strip()) for v in val.split(',') if v.strip()]
                except Exception:
                    pass
            else:
                val = [v.strip() for v in val.split(',') if v.strip()]
        elif option == 'active':
            val = not self.sequenceData.active
            self.sequenceData.active = val
            kodiutil.setGlobalProperty('ACTIVE', self.sequenceData.active and '1' or '0')
        elif option == 'type':
            if not self.sequenceData.get('type'):
                val = '2D'
            else:
                val = self.sequenceData.get('type') == '2D' and '3D' or ''
        else:
            val = xbmcgui.Dialog().input(u'Enter {0}'.format(label), self.sequenceData.get(option))

        if val is None:
            return

        self.sequenceData.set(option, val)
        self.modified = True
        self.updateItem(item)

    def updateItem(self, mli):
        o = mli.dataSource
        kodiutil.DEBUG_LOG(repr(o))
        if o[0] == 'active':

            kodiutil.DEBUG_LOG(repr(self.sequenceData.active))
            label2 = self.sequenceData.active and '[COLOR FF00FF00]YES[/COLOR]' or '[COLOR FFFF0000]NO[/COLOR]'
        elif o[0] == 'type':
            if self.sequenceData.get('type'):
                label2 = self.sequenceData.get('type') == '3D' and '3D' or '2D'
            else:
                label2 = 'ANY'
        elif o[0] in ('year', 'studios', 'directors', 'genres'):
            label2 = ','.join([str(y) for y in self.sequenceData.get(o[0], [])]) or None

        mli.setLabel(o[1])
        mli.setLabel2(label2)
        mli.setProperty('name', o[1])


def setAttributes(sequenceData):
    w = SeqAttrEditorDialog.open(sequence_data=sequenceData)
    return w.modified
