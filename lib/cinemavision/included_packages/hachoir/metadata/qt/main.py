from os.path import basename, dirname
from sys import argv, exit
from os import getcwd

from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QApplication, QDialog,
                         QTableWidgetItem, QFileDialog, QMessageBox)

from hachoir.metadata.qt.dialog_ui import Ui_Form
from hachoir.core import config
from hachoir.core.error import HACHOIR_ERRORS
from hachoir.core.cmd_line import unicodeFilename
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from hachoir.metadata.metadata import MultipleMetadata


config.quiet = True


class CustomTableWidgetItem(QTableWidgetItem):

    def __init__(self, parent=None):
        super(CustomTableWidgetItem, self).__init__(parent)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)


class MetadataError(Exception):

    def __init__(self, message):
        self.unicode_message = message
        bytes_message = message.encode("ASCII", "replace")
        Exception.__init__(self, bytes_message)

    def __unicode__(self):
        return self.unicode_message


class File:

    def __init__(self, filename, realname):
        self.name = filename
        if realname:
            self.realname = realname
        else:
            self.realname = filename
        try:
            self.parser = createParser(self.name, self.realname)
        except HACHOIR_ERRORS as err:
            raise MetadataError("Parser error: %s" % str(err))
        if not self.parser:
            raise MetadataError("Unable to parse the file: %s" % self.name)
        try:
            self.metadata = extractMetadata(self.parser)
        except HACHOIR_ERRORS as err:
            raise MetadataError("Metadata extraction error: %s" % str(err))
        if not self.metadata:
            file_type = self.parser.mime_type
            raise MetadataError(
                "Unable to extract metadata from file of type %s" % file_type)


class Metadata(QDialog, Ui_Form):

    def __init__(self, application):
        QDialog.__init__(self)
        self.application = application
        self.files = {}
        self.setupWindow()
        self.current_dir = dirname(getcwd())

    def setupWindow(self):
        self.setupUi(self)
        self.connect(self.open_button, SIGNAL("clicked()"), self.open)
        self.connect(self.quit_button, SIGNAL("clicked()"), self.quit)
        self.connect(
            self.files_combo,
            SIGNAL("currentIndexChanged(const QString&)"),
            self.changeFile)
        self.metadata_table.horizontalHeader().hide()
        self.metadata_table.verticalHeader().hide()

    def open(self):
        filename = QFileDialog.getOpenFileName(
            self,  # parent
            "Choose a file to open",  # caption
            self.current_dir,  # dir name
            "",  # filter
            "Any type"  # filter set
        )
        if not filename:
            return
        filename = str(filename)
        self.current_dir = dirname(filename)
        self.addFile(filename, change=True)

    def quit(self):
        self.application.quit()

    def fillList(self, file):
        table = self.metadata_table
        metadata = file.metadata
        groups = [metadata]
        if isinstance(metadata, MultipleMetadata):
            groups.extend(list(metadata.iterGroups()))
        total = 0
        for index, metadata in enumerate(groups):
            group_name = metadata.header
            metadata = [data for data in metadata if data.values]
            metadata.sort()
            if 0 < index:
                metadata.insert(0, group_name)
            groups[index] = metadata
            total += len(metadata)
        table.clear()
        table.setColumnCount(2)
        table.setRowCount(total)
        row = 0
        for metadata in groups:
            for data in metadata:
                if isinstance(data, str):
                    table.setItem(row, 0, CustomTableWidgetItem("-- group --"))
                    table.setItem(row, 1, CustomTableWidgetItem(data))
                    row += 1
                    continue
                title = data.description
                for item in data.values:
                    value = item.text
                    table.setItem(row, 0, CustomTableWidgetItem(title))
                    table.setItem(row, 1, CustomTableWidgetItem(value))
                    row += 1
        table.resizeColumnsToContents()

    def changeFile(self, name):
        name = str(name)
        file = self.files[name]
        self.fillList(file)

    def error(self, message):
        QMessageBox.warning(self, "Metadata error", message)

    def addFile(self, filename, realname=None, change=False):
        try:
            file = File(filename, realname)
        except MetadataError as err:
            errmsg = str(err)
            self.error(errmsg)
            return
        name = basename(file.name)
        self.files[name] = file
        self.files_combo.addItem(name)
        if change:
            index = self.files_combo.count() - 1
            self.files_combo.setCurrentIndex(index)


def main():
    app = QApplication(argv)
    metadata = Metadata(app)
    for filename in argv[1:]:
        realname = filename
        filename = unicodeFilename(filename)
        metadata.addFile(filename, realname)
    metadata.show()
    exitcode = app.exec_()
    exit(exitcode)
