import logging

import webview
from webview import Window

from lawchecker.lawchecker_logger import logger


class ProgressModal:
    @classmethod
    def static_update(
        cls, window: Window | None, text: str, log=False, log_level='INFO'
    ) -> None:
        """
        Method for updating progress modal from outside of context manager.
        This is for short on off updates, not for long running processes.
        """

        if window is None and webview.active_window() is not None:
            window = webview.active_window()
        elif window is None:
            logger.error('No active window found')
            return

        if log:
            try:
                getattr(logger, log_level.lower())(text)
            except AttributeError:
                logger.error(f'Invalid log level: {log_level}')
                logger.info(text)

        if isinstance(window, Window):
            window.evaluate_js(f'progress_modal_update({repr(text)})')

    def __init__(self, window: Window | None = None) -> None:
        if window is not None:
            self.window = window
        elif webview.active_window() is not None:
            self.window = webview.active_window()
        else:
            raise ValueError('No active window found')

    def __enter__(self):
        if isinstance(self.window, Window):
            self.window.evaluate_js('progress_modal_show()')
            self.window.evaluate_js('disable_progress_modal_ok_button_element()')

        return self

    def update(self, text: str, log=False, log_level='INFO') -> None:
        self.static_update(self.window, text, log, log_level)

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        if isinstance(self.window, Window):
            self.window.evaluate_js('enable_progress_modal_ok_button_element()')


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

        if not isinstance(message, str):
            message = repr(message)

        message = message.encode('unicode-escape').decode()

        if record.levelname == 'NOTICE':
            # Do not emit word NOTICE to the ui.
            message = f'{message}'
        else:
            message = f'{record.levelname}: {message}'

        # Pass `record.levelname` and `message` to modal
        ProgressModal.static_update(self.window, message)
