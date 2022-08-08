from wx import ListCtrl, EVT_WINDOW_CREATE, CallAfter
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class field_view_t(ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self):
        self.cols = {}

        ListCtrl.__init__(self)
        self.Bind(EVT_WINDOW_CREATE, self.on_create)

    def post_init(self):
        ListCtrlAutoWidthMixin.__init__(self)

        columns = ['address', 'name', 'type', 'size', 'data', 'description']
        for name in columns:
            self.append_column(name)
        self.col_min_width = [len(s) for s in columns]

        self.Layout()
        self.dispatcher.trigger('field_view_ready', self)

    def on_create(self, event):
        self.Unbind(EVT_WINDOW_CREATE)
        CallAfter(self.post_init)

    def append_column(self, name):
        index = self.GetColumnCount()
        self.cols[name] = index
        self.InsertColumn(col=index, heading=name)

    def get_selected(self, name):
        return self.GetItem(self.GetFocusedItem(), self.cols['name']).GetText()

    def clear(self):
        self.DeleteAllItems()

    def register_callback(self, cbGetItemText):
        self.OnGetItemText_imp = cbGetItemText

    def OnGetItemText(self, item, col):
        return self.OnGetItemText_imp(item, col)

    def get_col_index(self, name):
        return self.cols[name]

    def get_col_count(self):
        return len(self.cols)

    def resize_column(self, col_index, width):
        width = max(self.col_min_width[col_index], width) + 1
        self.SetColumnWidth(col_index, self.GetCharWidth() * width)
