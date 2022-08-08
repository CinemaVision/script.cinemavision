"""
Binary striper: remove metadata, producer information, useless padding, etc.
from binary files.

Author: Victor Stinner
Creation: 17 september 2006
"""

from hachoir.field import MissingField
from hachoir.editor import createEditor
from hachoir.stream import FileOutputStream, StringOutputStream
from hachoir.core.tools import humanFilesize
from hachoir.core.cmd_line import displayVersion
from hachoir.parser import createParser
from optparse import OptionGroup, OptionParser
import sys

# File formats
from hachoir.parser.archive import TarFile
from hachoir.parser.audio import AuFile
from hachoir.parser.image import PngFile, JpegFile
from hachoir.parser.container import RiffFile
from hachoir.parser.audio import MpegAudioFile

# Strip what?
STRIP_USELESS = 0x01    # Useless padding, useless duplicate information, etc.
STRIP_METADATA = 0x02   # Timestamp, author, producter, comment, etc.
STRIP_INDEX = 0x04      # Index in video


class BasicStripper:

    def __init__(self, editor, level, verbose=False):
        self.editor = editor
        self.level = level
        self.verbose = verbose
        self._is_dirty = False
        self._removed_bytes = 0

    def __call__(self):
        self.stripped_bytes = self.strip()
        if self.stripped_bytes:
            self._is_dirty = True
        return self._is_dirty

    def info(self, message):
        if self.verbose:
            print(message)

    def strip(self):
        """
        Strip input editor. Returns number of remove bits.
        """
        raise NotImplementedError()

    def removeField(self, field, editor=None):
        if not editor:
            editor = self.editor
        self.info("Remove field %s" % field.path)
        size = field.size
        del editor[field.name]
        return size

    def removeFields(self, fields, editor=None):
        if not editor:
            editor = self.editor
        return sum(self.removeField(field, editor) for field in fields)


class CheckStripper(BasicStripper):

    def checkField(self, field):
        """
        Check if a field of the root have to be removed or not.
        Returns boolean.
        """
        raise NotImplementedError()

    def strip(self):
        fields = (field for field in self.editor if self.checkField(field))
        return self.removeFields(fields)


class PngStripper(CheckStripper):

    def checkField(self, field):
        if self.level & STRIP_METADATA:
            name = field.name
            if name.startswith("text["):
                return True
            if name == "time":
                return True
        return False


class JpegStripper(CheckStripper):

    def checkField(self, field):
        if self.level & STRIP_METADATA:
            if field.name.startswith("comment"):
                return True
            return field.name in ("photoshop", "exif", "adobe")
        return False


class MpegAudioStripper(CheckStripper):

    def checkField(self, field):
        if self.level & STRIP_METADATA:
            return field.name in ("id3v1", "id3v2")
        return False


class AuStripper(BasicStripper):

    def strip(self):
        if self.level & STRIP_METADATA and "info" in self.editor:
            size = self.editor["info"].size
            self.editor["data_ofs"].value -= (size // 8)
            return self.removeField(self.editor["info"])
        else:
            return 0


class RiffStripper(BasicStripper):

    def stripSub(self, editor, names):
        remove = []
        total = 0
        for field in editor:
            if field.name in names:
                remove.append(field)
                continue
            try:
                tag = field["tag"].value
            except MissingField:
                continue
            if self.level & STRIP_USELESS and tag in "JUNK":
                remove.append(field)
                continue
            if tag == "LIST" and field.name != "movie":
                # Strip a chunk list
                size = self.stripSub(field, names)
                if size:
                    # Update chunk list size
                    field["size"].value -= (size // 8)
                total += size
        total += self.removeFields(remove, editor)
        return total

    def strip(self):
        names = []
        if self.level & STRIP_USELESS:
            names.append("nb_sample")
        if self.level & STRIP_METADATA:
            names.append("info")
        if self.level & STRIP_INDEX:
            if "/headers/avi_hdr/has_index" in self.editor:
                self.editor["/headers/avi_hdr/has_index"].value = False
            names.append("index")
        size = self.stripSub(self.editor, names)
        if size:
            # Update file size field
            self.editor["filesize"].value -= (size // 8)
        return size


def usage():
    print("Usage: %s filename" % sys.argv[0])


class TarStripper(BasicStripper):

    def strip(self):
        for file in self.editor.array("file"):
            self.stripFile(file)

    def fixChecksum(self, file):
        file["check_sum"].value = " " * 8
        stream = StringOutputStream()
        file.writeInto(stream)
        data = stream.readBytes(0, 512)
        checksum = sum(ord(character) for character in data)
        file["check_sum"].value = ("0%o\0" % checksum).ljust(8, " ")

    def stripFile(self, file):
        empty32 = "\0" * 32
        uid = "0000000\0"
        file["uid"].value = uid
        file["gid"].value = uid
        file["mtime"].value = "00000000000\0"
        file["uname"].value = empty32
        file["gname"].value = empty32
        self.fixChecksum(file)
        self._is_dirty = True


strippers = {
    AuFile: AuStripper,
    RiffFile: RiffStripper,
    PngFile: PngStripper,
    JpegFile: JpegStripper,
    MpegAudioFile: MpegAudioStripper,
    TarFile: TarStripper,
}


def stripEditor(editor, filename, level, verbose):
    cls = editor.input.__class__
    try:
        stripper_cls = strippers[cls]
    except KeyError:
        print("Don't have stripper for file type: %s" % editor.description)
        return False
    stripper = stripper_cls(editor, level, verbose)

    if stripper():
        output = FileOutputStream(filename)
        with output:
            editor.writeInto(output)

        size = stripper.stripped_bytes
        if size:
            percent = "%.1f%%" % (float(size) * 100 / editor.input.size)
            if size % 8 and size < 128:
                print("Remove %u.%u bytes (%s)"
                      % (size // 8, size % 8, percent))
            else:
                print("Remove %s (%s)" % (humanFilesize(size // 8), percent))
        print("Save new file into %s" % filename)
    else:
        print("Stripper doesn't touch the file")
    return True


def parseOptions():
    parser = OptionParser(usage="%prog [options] filename")

    common = OptionGroup(parser, "Hachoir strip")
    common.add_option("--strip",
                      help="Data types to remove: "
                           "useless, metadata, index (default: all). "
                           "Use comma to specify two or more.",
                      type="str", action="store",
                      default="metadata, useless, index")
    common.add_option("--quiet", help="Be quiet",
                      action="store_true", default=False)
    common.add_option("--version", help="Display version and exit",
                      action="callback", callback=displayVersion)
    parser.add_option_group(common)

    values, arguments = parser.parse_args()
    if not arguments:
        parser.print_help()
        sys.exit(1)
    return values, arguments


def main():
    # Parse arguments and read filenames
    values, filenames = parseOptions()
    level = 0
    for item in values.strip.split(","):
        item = item.strip()
        if item == "useless":
            level |= STRIP_USELESS
        elif item == "metadata":
            level |= STRIP_METADATA
        elif item == "index":
            level |= STRIP_INDEX
    if not level:
        print("Nothing to do, exit")
        sys.exit(0)
    ok = True
    for filename in filenames:
        print("[+]", ("Process file %s" % filename))
        parser = createParser(filename)
        if parser:
            editor = createEditor(parser)
            ok &= stripEditor(editor, filename + ".new",
                              level, not(values.quiet))
        else:
            ok = False
    if ok:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
