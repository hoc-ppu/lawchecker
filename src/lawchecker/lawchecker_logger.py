import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

"""
Create logger and handlers that all classes and functions can tap into.
"""

logger = logging.getLogger("LawChecker")
logger.setLevel(logging.DEBUG)  # Set the logger's level to DEBUG

log_file_path = Path("logs", os.getlogin(), "LawChecker.log").resolve()
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# create file handler which logs even debug messages
fh = RotatingFileHandler(
    str(log_file_path), mode="a", maxBytes=1024 * 1024
)
fh.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(level=logging.WARNING)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    "%Y-%m-%d %H:%M:%S",  # dont't want milliseconds
)

# add formatter to the file/console handlers
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
