from wx import App, EVT_MENU, ID_OK
from wx.xrc import XRCID

import hachoir.core.config as config
from hachoir.parser.guess import createParser, guessParser
from hachoir.stream.input import FileFromInputStream
from hachoir.wx.dispatcher import dispatcher_t
from hachoir.wx import frame_view, field_view, hex_view, tree_view
from hachoir.wx.dialogs import file_open_dialog
from hachoir.wx.unicode import force_unicode
from hachoir import __version__


class app_t(App):
    def __init__(self, filename=None):
        print("[+] Run hachoir-wx version %s" % __version__)
        self.filename = filename
        App.__init__(self, False)

    def OnInit(self):
        self.bind_events()

        if self.filename:
            load_file(self, self.filename)
        else:
            self.on_file_menu_open_file(None)

        return True

    def bind_events(self):
        self.Bind(EVT_MENU, self.on_file_menu_open_file,
                  id=XRCID('file_menu_open_file'))
        self.Bind(EVT_MENU, self.on_file_menu_close_window,
                  id=XRCID('file_menu_close_window'))

    def on_file_menu_open_file(self, event):
        open_dialog = file_open_dialog()
        if ID_OK != open_dialog.ShowModal():
            return
        filename = open_dialog.GetPath()
        open_dialog.Destroy()
        load_file(self, filename)

    def on_field_parse_substream(self, dispatcher, field):
        stream = field.getSubIStream()
        parser = guessParser(stream)
        if not parser:
            msg = '[-] Unable to parse substream.'
            if not config.verbose:
                msg += ' (use --verbose to see validation errors)'
            print(msg)
            return
        print('[+] Substream parser: %s.%s' % (parser.__module__, type(parser).__name__))
        subfile = FileFromInputStream(stream)
        subfile.name = field.path
        new_window(self, subfile, parser, subfile.name)

    def on_field_open_window_here(self, dispatcher, field):
        new_window(self, dispatcher.top_file, field, dispatcher.top_filename)

    def on_frame_activated(self, dispatcher, frame):
        self.SetTopWindow(frame)

    def on_file_menu_close_window(self, event):
        top_window = self.GetTopWindow()
        assert top_window is not None
        top_window.Close()


def load_file(app, filename):
    parser = createParser(force_unicode(filename), real_filename=filename)
    if not parser:
        return
    print('[+] Using parser: %s.%s' % (parser.__module__, type(parser).__name__))
    new_window(app, open(filename, 'rb'), parser, filename)


def new_window(app, file, parser, filename):
    print('[+] Opening new GUI')

    dispatcher = dispatcher_t()
    dispatcher.add_receiver(app)
    dispatcher.top_file = file
    dispatcher.top_filename = filename

    frame = frame_view.setup_frame_view(dispatcher)
    field_view.setup_field_view(frame, dispatcher)
    hex_view_widget = hex_view.setup_hex_view(frame, dispatcher)
    tree_view.setup_tree_view(frame, dispatcher)

    dispatcher.trigger('file_ready', file)
    dispatcher.trigger('field_set_ready', parser)
    dispatcher.trigger('filename_update', filename.replace('\\', '/'))
    frame.ready()
    hex_view_widget.ready()

    frame.Show()
    print('[+] GUI ready')
