import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE_PATH = Path("logs", os.getlogin(), "check_amendments3.log").resolve()
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("check_amendments2")
logger.setLevel(logging.DEBUG)

# create formatter for the below handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# create file handler which logs even debug messages
fh = RotatingFileHandler(str(LOG_FILE_PATH), mode="a", maxBytes=1024 * 1024)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# console handler logs only warnings and above
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)
