import logging

from webview import Window


class ProgressModal:

    def __init__(self, window: Window) -> None:
        self.window = window

    def __enter__(self):

        if isinstance(self.window, Window):

            self.window.evaluate_js("progress_modal_show()")
            self.window.evaluate_js("disable_progress_modal_ok_button_element()")

        return self

    def update(self, text: str) -> None:

        if isinstance(self.window, Window):

            self.window.evaluate_js(f"progress_modal_update({repr(text)})")

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:

        if isinstance(self.window, Window):

            self.window.evaluate_js("enable_progress_modal_ok_button_element()")

class UILogHandler(logging.StreamHandler):
    """
    Custom handler for passing logs to `pywebview` UI.
    """

    def __init__(self, stream, window: Window) -> None:
        super().__init__(stream)
        self.window = window

    def emit(self, record) -> None:
        """
        Expects `record.msg` to be structured
        something like this, to allow for flexibility in the way it gets displayed
        in a UI:

            Main part of log message as one or more sentences. [Optional extended
            log message in square brackets giving more information. `Code can be
            surrounded by backticks`]

        The main part of the log message is extracted as `message`. The contents of
        the square brackets are extracted as `message_extended`.
        """

        # Default `message` is the whole of `record.msg`
        message = record.msg

        # Pass `record.levelname` and `message` to modal
        with ProgressModal(self.window) as modal:

            modal.update(
                f"{record.levelname}: {message.encode('unicode-escape').decode()}"
            )
