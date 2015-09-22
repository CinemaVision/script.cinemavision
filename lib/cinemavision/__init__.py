import included_packages

import util
import content
import sequence
import actions
import sequenceprocessor


def init(debug, progress=None, localizer=None):
    util.DEBUG = debug
    util.Progress = progress or util.Progress
    util.T = localizer or util.T
