import os
from pathlib import Path

from lawchecker.submodules.python_toolbox import _pp_log_base as pp_log_base

log_file_path = Path("logs", os.getlogin(), "LawChecker.log").resolve()

pp_logger = pp_log_base.PpLogger(
    log_file_path=log_file_path, inc_code_location=False
)

logger = pp_logger.logger
