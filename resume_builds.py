# Resumes builds that are in the pipeline directory when the script needs to
# restart. Starts make in the corresponding directories in case they had
# not finished.

from threading import Thread
import logging

from config import Config
from build import Build
from utils import get_build_directories

log = logging.getLogger('pipeline.' + __name__)


def resume_builds():
    builds = {}
    def resume_worker():
        for d in get_build_directories(Config.builds_dir):
            log.info("Reattaching build in directory %s", d)
            build = builds[d] = Build(None, None, init_from_hash=d)
            Build.run(build, 'xml')
    t = Thread(target=resume_worker, args=[])
    t.start()
    return builds
