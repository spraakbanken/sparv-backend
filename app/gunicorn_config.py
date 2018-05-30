import os
try:
    from config import Config
except ImportError:
    from config_default import Config

# Log to console if run with Docker, else to gunicorn.log
if not Config.run_docker:
    errorlog = os.path.join(Config.log_dir, "gunicorn.log")

timeout = 200           # workers silent for more than this many seconds are killed and restarted
bind = '0.0.0.0:8000'   # the socket to bind
workers = 1             # number of worker process for handling requests
