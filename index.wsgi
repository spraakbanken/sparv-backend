# -*- mode: python; coding: utf-8 -*-
import sys
import os
import logging

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

from config import Config
from utils import mkdir

################################################################################
# Pythonpaths to the sb python directory, and to the the directory of this script.
paths = [Config.sparv_python, Config.sparv_backend]

# The log file location. Set this to None if you rather want to log to stdout
log_file_location = Config.log_file
if __name__ == "__main__":
    log_file_location = None
################################################################################

# Create builds directory
if not os.path.exists(Config.builds_dir):
    mkdir(Config.builds_dir)

# Create logdir if it does not exist
if log_file_location:
    log_file_dir = os.path.dirname(log_file_location)
    if not os.path.exists(log_file_dir):
        mkdir(log_file_dir)

# Activate virtual environment
if Config.venv_path:
    activate_this = os.path.join(THIS_DIR, Config.venv_path)
    execfile(activate_this, dict(__file__=activate_this))

logging.basicConfig(filename=log_file_location, format="%(asctime)-15s %(message)s")
log = logging.getLogger('pipeline')
log.setLevel(logging.INFO)
log.info("Restarted index.wsgi")

# Setting the path
for path in paths:
    if path not in sys.path:
        sys.path.append(path)

os.environ['PYTHONPATH'] = ":".join(filter(lambda s: s, sys.path))

# Loading handlers
try:
    from handlers import handlers, handler_content_type
except:
    log.exception("Failed to import handlers")

# Import make_trace
try:
    from make_trace import make_trace
except:
    log.exception("Failed to import trace")

# Ongoing and finished builds
try:
    from resume_builds import resume_builds
    builds = resume_builds()
except:
    log.exception("Failed to resume builds")
    builds = dict()

# Global request counter
requests = 0


def application(environ, start_response):
    """
    Handles the incoming request
    """

    global requests
    requests += 1
    request = int(requests)

    path = environ.get('PATH_INFO', "")
    cmd = path.rstrip('/')

    log.info("Handling %s (request %s)" % (path, request))

    status = "200 OK"

    # for file upload
    if environ['REQUEST_METHOD'] == 'OPTIONS':
        response_headers = [('Content-type', 'text/plain'),
                            ('Access-Control-Allow-Origin', '*'),
                            ("Allow", "POST")]
        start_response(status, response_headers)
        return ['']

    else:
        response_headers = [('Content-Type', handler_content_type(path)),
                            ('Access-Control-Allow-Origin', '*'),
                            ("Allow", "POST")]
        if cmd == "/download":
            if environ["QUERY_STRING"].endswith(Config.fileupload_ext):
                response_headers.append(('Content-Disposition', 'attachment; filename="korpus.zip"'))
            else:
                response_headers.append(('Content-Disposition', 'attachment; filename="korpus.xml"'))

        start_response(status, response_headers)

    def unknown():
        yield "No handler for path %s\n" % path

    try:
        return handlers(builds, environ).get(cmd, unknown)()
    except:
        log.exception("Error in handler code")
        return ["Error in handler code: %s\n", make_trace()]


if __name__ == "__main__":
    """
    For local testing. Prefers to use eventlet because it handles concurrent
    requests, otherwise falls back on the wsgi reference implementation.
    """
    try:
        import eventlet
        from eventlet import wsgi
        log.info("Eventlet: monkey patching")
        eventlet.monkey_patch()
        log.info("Eventlet: starting server")
        wsgi.server(eventlet.listen(("", 8051)), application, minimum_chunk_size=1, max_size=100, keepalive=True)
    except ImportError, NameError:
        log.exception("Cannot find eventlet, resorting to wsgiref")
        from wsgiref.simple_server import make_server
        httpd = make_server("", 8051, application)
        httpd.serve_forever()
