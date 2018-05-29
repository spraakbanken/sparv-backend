# -*- mode: python; coding: utf-8 -*-
# from past.builtins import execfile
import sys
import os
import logging

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

from importlib import util as importutil
if importutil.find_spec("config") is None:
    # print "copy config_default.py to config.py and add your settings"
    from shutil import copyfile
    copyfile(os.path.join(THIS_DIR, "config_default.py"), os.path.join(THIS_DIR, "config.py"))

from config import Config
from utils import mkdir, make_trace

# Pythonpaths to the sb python directory, and to the the directory of this script.
paths = [Config.sparv_python, Config.sparv_backend]
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

os.environ['PYTHONPATH'] = ":".join([s for s in sys.path if s])

# Create builds directory
if not os.path.exists(Config.builds_dir):
    mkdir(Config.builds_dir)

# Setup logging
if __name__ == "__main__":
    # Log to stdout if this script is run locally
    Config.log_dir = None
import logger  # import needed for logging to log file!
log = logging.getLogger('pipeline')
log.info("Restarted index.wsgi")

# # Activate virtual environment
# activate_this = os.path.join(THIS_DIR, Config.venv_path)
# execfile(activate_this, dict(__file__=activate_this))

# Load ongoing and finished builds
try:
    from resume_builds import resume_builds
    builds = resume_builds()
except:
    log.exception("Failed to resume builds")
    builds = dict()


def application(env, resp):
    """
    Wrapper for the flask application.
    It is best run with gunicorn.
    All routes are specified in handlers.py
    """
    try:
        from handlers import app as real_app
        env['SCRIPT_NAME'] = ''

        # Save builds in app
        real_app.config["BUILDS"] = builds

        # Set global request counter
        if "N_REQUESTS" not in real_app.config:
            real_app.config["N_REQUESTS"] = 0

        return real_app(env, resp)

    except:
        log.exception("Error while running application.")
        return ["Error while running application: %s\n", make_trace()]


if __name__ == "__main__":
    """
    For local testing. Run with gunicorn otherwise since
    waitress does not support continuous response streaming.
    """
    from waitress import serve
    serve(application, host='0.0.0.0', port=8080)
