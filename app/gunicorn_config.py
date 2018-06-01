import os
import sys

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

try:
    from config import Config
except ImportError:
    from config_default import Config

errorlog = Config.gunicorn_errorlog
timeout = Config.gunicorn_timeout
bind = Config.gunicorn_bind
workers = Config.gunicorn_workers
