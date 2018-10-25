# -*- mode: python; coding: utf-8 -*-
import sys
import os
import logging

try:
    from config import Config
except ImportError:
    from config_default import Config

# Pythonpaths to the sparv python directory, and to the the directory of this script
paths = [Config.sparv_python, Config.sparv_backend]
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

from utils import mkdir, make_trace

# Create builds directory
if not os.path.exists(Config.builds_dir):
    mkdir(Config.builds_dir)

# Setup logging
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
        from handlers import app
        # env['SCRIPT_NAME'] = ''

        # Save builds in app
        app.config["BUILDS"] = builds

        # Set global request counter
        if "N_REQUESTS" not in app.config:
            app.config["N_REQUESTS"] = 0

        app.config["JSON_SORT_KEYS"] = False

        return app(env, resp)

    except:
        log.exception("Error while running application.")
        return ["Error while running application: %s\n", make_trace()]


if __name__ == "__main__":
    """
    For local testing. Run with gunicorn otherwise to get
    continuous response streaming.
    """
    # Serve with Waitress
    # from waitress import serve
    # serve(application, host=Config.wsgi_host, port=Config.wsgi_port)

    # Serve directly with Flask
    from handlers import app
    # Save builds in app
    app.config["BUILDS"] = builds
    # Set global request counter
    if "N_REQUESTS" not in app.config:
        app.config["N_REQUESTS"] = 0

    app.config["JSON_SORT_KEYS"] = False
    app.run(debug=True, threaded=True, host=Config.wsgi_host, port=Config.wsgi_port)
