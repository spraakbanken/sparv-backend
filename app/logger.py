import logging
import sys
import os.path
import time
import stat
from config import Config

# Set debug level: DEBUG, INFO, WARNING, ERROR, CRITICAL
DEBUGLEVEL = logging.INFO

# Format for log messages and date
LOGFMT = '%(asctime)-15s - %(levelname)s: %(message)s'
DATEFMT = '%Y-%m-%d %H:%M:%S'

if getattr(Config, "log_dir", False):
    today = time.strftime("%Y%m%d")
    DEBUGFILE = os.path.join(Config.log_dir, '%s-backend.log' % today)
    # Create Logfile if it does not exist
    if not os.path.isfile(DEBUGFILE):
        with open(DEBUGFILE, "w") as f:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("%s CREATED DEBUG FILE\n\n" % now)
            # Fix permissions
            os.chmod(DEBUGFILE, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
            stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            logging.basicConfig(filename=DEBUGFILE, level=DEBUGLEVEL,
            format=LOGFMT, datefmt=DATEFMT)
else:
    logging.basicConfig(stream=sys.stdout, level=DEBUGLEVEL,
                        format=LOGFMT, datefmt=DATEFMT)
