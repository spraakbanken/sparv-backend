import os
import sys

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

from config import Config
errorlog = os.path.join(Config.log_dir, "gunicorn.log")

timeout = 200           # workers silent for more than this many seconds are killed and restarted
bind = '0.0.0.0:8801'   # the socket to bind
workers = 2             # number of worker process for handling requests
