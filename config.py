################################################################################
#
# Configuration of paths
#
################################################################################
import os


class Config(object):
    """Static settings"""

    # Backend adress
    backend = "https://ws.spraakbanken.gu.se/ws/sparv/v1"

    # Path to pipeline (not necessary, only used within this script)
    pipeline_dir = os.path.join(os.path.dirname(__file__), "pipeline")

    # Pythonpaths to the sb python directory, and to the the directory of this script:
    sparv_python = os.path.join(pipeline_dir, 'python')
    sparv_backend = os.path.dirname(__file__)

    # Where the pipeline working directory is located
    builds_dir = os.path.join(os.path.dirname(__file__), 'builds')

    # The log file location. Set this to None if you rather want to log to stdout
    log_dir = os.path.join(builds_dir, 'log')
    log_file = os.path.join(log_dir, 'backend.log')

    # Where the models and makefiles are hosted (SPARV_MODELS, SPARV_MAKEFILES)
    sparv_models = os.path.join(pipeline_dir, 'models')
    sparv_makefiles = os.path.join(pipeline_dir, 'makefiles')

    # Secret key for dangerous queries
    secret_key = ""

    # Path to python virtual environment (optional, set to None if not applicable)
    venv_path = os.path.join(sparv_backend, 'venv/bin/activate_this.py')

    # The number of processes (sent as a -j flag to make)
    processes = 2

    # Location of the JSON schema for makefile settings
    sv_schema = os.path.join(sparv_backend, 'settings_schema_sv.json')
    sv_dev_schema = os.path.join(sparv_backend, 'settings_schema_sv-dev.json')
    fl_schema = os.path.join(sparv_backend, 'settings_schema_fl.json')  # FreeLing
    tt_schema = os.path.join(sparv_backend, 'settings_schema_tt.json')

    api_json = os.path.join(sparv_backend, 'api.json')

    # Socket file
    socket_file = os.path.join(builds_dir, 'pipeline.sock')

    # The catalaunch binary
    catalaunch_binary = os.path.join(builds_dir, 'catalaunch')

    # The "python" interpreter, replaced with catalaunch
    python_interpreter = catalaunch_binary + " " + socket_file
