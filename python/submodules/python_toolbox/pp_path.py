"""
Little utility functions for common tasks like checking paths; creating/deleting
directories; etc.
"""

from os import mkdir, path
from shutil import rmtree

from . import pp_log


def is_valid_directory_path(user_input: str) -> bool:

    if path.isdir(user_input):

        pp_log.logger.info(f"<{user_input}> is a valid directory path.")

        return True

    pp_log.logger.error(
        f"<{user_input}> is not a valid directory path, please try again."
    )

    return False


def is_valid_file_path(user_input: str) -> bool:

    if path.isfile(user_input):

        pp_log.logger.info(f"<{user_input}> is a valid file path.")

        return True

    pp_log.logger.error(f"<{user_input}> is not a valid file path, please try again.")

    return False


def create_directory(directory_path: str) -> bool:

    return_value = False

    try:

        mkdir(directory_path)

        pp_log.logger.info(f"Created directory <{directory_path}>.")

        return_value = True

    except Exception:

        pp_log.logger.error(f"Could not create directory <{directory_path}>.")

    return return_value


def delete_directory_and_contents(directory_path: str) -> bool:

    return_value = False

    try:

        rmtree(directory_path, ignore_errors=False)

        pp_log.logger.info(f"Deleted directory <{directory_path}> and its contents.")

        return_value = True

    except (Exception):

        pp_log.logger.error(f"Could not delete directory <{directory_path}>.")

    return return_value
