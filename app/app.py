# -*- mode: python; coding: utf-8 -*-
# from past.builtins import execfile
import sys
import os
import logging

from utils import mkdir, make_trace
try:
    from config import Config
except ImportError:
    from config_default import Config

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
