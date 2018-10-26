################################################################################
#
# Configuration of paths
#
################################################################################
from builtins import object
import os
from pathlib import Path
import logging


class Config(object):
    """Static settings"""

    # Backend adress
    backend = 'localhost:8000'
    wsgi_host = '0.0.0.0'
    wsgi_port = 8801

    # Secret key for dangerous queries
    secret_key = ""

    # URL and API version number that will be displayed in the documentation
    api_url = "https://ws.spraakbanken.gu.se/ws/sparv/v3"
    api_version = "3.0"

    # Path to pipeline (not necessary, only used within this script)
    pipeline_dir = os.path.join(str(Path(__file__).parents[1]), 'data', 'sparv-pipeline')

    # Pythonpaths to the sb python directory, and to the the directory of this script:
    sparv_python = pipeline_dir
    sparv_backend = os.path.dirname(__file__)

    # Where the pipeline working directory is located
    builds_dir = os.path.join(str(Path(__file__).parents[1]), 'data', 'builds')

    # The log file location. Set this to None if you rather want to log to stdout
    log_dir = os.path.join(str(Path(__file__).parents[1]), 'logs')
    # Set debug level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    debuglevel = logging.INFO

    # Where the models and makefiles are hosted (SPARV_MODELS, SPARV_MAKEFILES)
    sparv_models = os.path.join(pipeline_dir, 'models')
    sparv_makefiles = os.path.join(pipeline_dir, 'makefiles')

    # Path to python virtual environment
    # (optional, not needed when running with Docker or when venv is activated manually)
    # venv_path = os.path.join(os.path.dirname(__file__), 'venv')

    # The number of processes (sent as a -j flag to make)
    processes = 2

    # Extension for file upload hash
    fileupload_ext = "-f"

    # Socket file
    socket_file = os.path.join(builds_dir, 'pipeline.sock')

    # The catalaunch binary
    catalaunch_binary = os.path.join(builds_dir, 'catalaunch')

    # The "python" interpreter, replaced with catalaunch
    python_interpreter = catalaunch_binary + " " + socket_file

    ############################################################################
    # Gunicorn config
    if log_dir:
        gunicorn_errorlog = os.path.join(log_dir, "gunicorn.log")  # gunicorn log file.
    else:
        gunicorn_errorlog = None
    gunicorn_timeout = 200  # workers silent for more than this many seconds are killed and restarted
    gunicorn_workers = 1    # number of worker process for handling requests
    ############################################################################
