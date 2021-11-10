from . import included_packages

from . import util
from . import content
from . import sequence
from . import actions
from . import sequenceprocessor


def init(debug, progress=None, localizer=None, tags_3D_regex=''):
    util.DEBUG = debug
    util.Progress = progress or util.Progress
    util.T = localizer or util.T
    util.TAGS_3D_REGEX = tags_3D_regex
