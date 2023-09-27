"""
Small utility functions and wrappers for built-in functions to provide a friendlier
command line interface for users.
"""

from . import pp_log
from . import pp_path


def clear() -> None:
    """
    Clear the terminal console.
    """

    # Clear console
    print("\033[2J")


def input_text(prompt: str) -> str:
    """
    Prompt for user text input.
    """

    user_input = input(f"{prompt}: ")

    return user_input


def input_integer(prompt: str) -> int:
    """
    Prompt for user interger input.
    """

    while True:

        try:

            user_input = int(input_text(prompt))

            break

        except ValueError:

            pp_log.logger.error("A number was expected.")

        except Exception as e:

            pp_log.logger.critical(f"An unexpected error occurred: {e}")

    return user_input


def input_list_selection(prompt: str, options: list) -> int | None:
    """
    Present a numbered list of options for the user to choose from.
    """

    options_len = len(options)

    if options_len < 1:

        pp_log.logger.error("Trying to display a list with no options.")

        return None

    print(f"{prompt}:")

    # Start a counter from 1, for numbering the options
    i = 1

    for option in options:

        print(f"    {i}: {option}")

        i = i + 1

    while True:

        user_input = input_integer(f"Enter 1-{options_len}: ")

        if (user_input >= 1) and (user_input <= options_len):

            return_value = user_input

            break

        else:

            pp_log.logger.error(f"Entered value was not valid. Enter 1-{options_len}.")

    return return_value


def input_file_path(prompt: str) -> str:
    """
    Prompt user to enter a valid file path.
    """

    while True:

        user_input = input_text(prompt)

        if pp_path.is_valid_file_path(user_input) is True:

            return_value = user_input

            break

    return return_value


def input_directory_path(prompt: str) -> str:
    """
    Prompt user to enter a valid directrory path.
    """

    while True:

        user_input = input_text(prompt)

        if pp_path.is_valid_directory_path(user_input) is True:

            return_value = user_input

            break

    return return_value
