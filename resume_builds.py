# Resumes builds that are in the pipeline directory when the script needs to
# restart. Starts make in the corresponding directories in case they had
# not finished.

from threading import Thread

import logging
import os

from config import Config
from build import Build

log = logging.getLogger('pipeline.' + __name__)

def get_immediate_subdirectories(directory):
    return os.walk(directory).next()[1]

def resume_builds():
    builds = {}
    for d in get_immediate_subdirectories(Config.builds_dir):
        log.info("Reattaching build in directory %s", d)
        build = builds[d] = Build(None, None, init_from_hash=d)
        t = Thread(target=Build.run, args=[build, "xml"])
        t.start()
    return builds
