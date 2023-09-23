"""
Custom setup and extensions to built-in classes to provide friendly logging
and command-line feedback.
"""

import logging
import os

from logging.handlers import RotatingFileHandler


LOG_NAME = "pp_log"


AVAILABLE_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class FileFormatter(logging.Formatter):
    """
    Custom formatting for log entries appended to the log file.
    """

    def format(self, record):

        format = (
            "%(asctime)s "
            + record.levelname.capitalize()
            + ": "
            + "%(message)s "
            + "(`%(funcName)s` in `%(filename)s`, line %(lineno)d)"
        )

        formatter = logging.Formatter(format)

        return formatter.format(record)


class ConsoleFormatter(logging.Formatter):
    """
    Custom formatting for log entries printed to the console.
    """

    colours = {
        "DEBUG": "\033[90m",
        "INFO": "\033[94m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[91m",
    }

    def format(self, record):

        format = (
            "    "
            + self.colours.get(record.levelname, "\033[0m")
            + record.levelname.capitalize()
            + ": "
            + "\033[0m"
            + "%(message)s"
        )

        formatter = logging.Formatter(format)

        return formatter.format(record)


# Create a new logger
logger = logging.getLogger(LOG_NAME)

# Set the default logging levels (we can override this for different handlers later)
logger.setLevel(logging.DEBUG)


"""
Configure logging to file.
"""

# Get path to user's home directory
user_profile_path = os.environ["USERPROFILE"]

# Append ".logs" to `user_profile_path`
log_directory_path = os.path.join(user_profile_path, ".logs")

# If directory at `log_directory_path` doesn't already exist...
if os.path.isdir(log_directory_path) is False:

    # Create `log_directory_path`
    os.mkdir(log_directory_path)

# Append log file name to `log_directory_path`
log_file_path = os.path.join(log_directory_path, "pp_python_tools.log")

# Set `log_file_path` to be the log file; append log entries to the end of the file;
# trim the file when it gets to 1MB in size
log_handler_file = RotatingFileHandler(
    str(log_file_path), mode="a", maxBytes=(1024 * 1024)
)

# Create a new log formatter
log_formatter_file = FileFormatter()

# Apply `log_formatter_file` to `log_handler_file`
log_handler_file.setFormatter(log_formatter_file)

# Add `log_handler_file` to `logger`
logger.addHandler(log_handler_file)


"""
Configure logging to console.
"""

log_handler_console = logging.StreamHandler()

# Create a new log formatter
log_formatter_console = ConsoleFormatter()

# Apply `log_formatter_console` to `log_handler_console`
log_handler_console.setFormatter(log_formatter_console)

# Add `log_handler_console` to `logger`
logger.addHandler(log_handler_console)


def set_file_level(level: str) -> None:

    if level in AVAILABLE_LEVELS:

        log_handler_file.setLevel(AVAILABLE_LEVELS[level])


def set_console_level(level: str) -> None:

    if level in AVAILABLE_LEVELS:

        log_handler_console.setLevel(AVAILABLE_LEVELS[level])
