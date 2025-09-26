import sys
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from lxml import etree

from lawchecker.lawchecker_logger import logger

WEBVIEW_WINDOW: None | Any = None


class RtEnv(Enum):
    EXE = 1  # running from a pyInstaller single file .exe
    APP = 2  # running from a py2app app bundle
    SCRIPT = 3  # with default unbundled interpreter


RUNTIME_ENV = RtEnv.SCRIPT  # by default assume running as a script

if hasattr(sys, 'executable') and hasattr(sys, '_MEIPASS'):
    # we are using the bundled app on windows
    RUNTIME_ENV = RtEnv.EXE
elif hasattr(sys, 'frozen') and Path('../Resources').exists():
    # we are using the bundled app on macos
    RUNTIME_ENV = RtEnv.APP


try:
    # on the bundled app we expect the /env file to be in the temp folder
    bundled_env = Path(sys._MEIPASS).joinpath('.env')  # type: ignore
    if bundled_env.exists():
        secrets = dotenv_values(bundled_env)
    else:
        raise Exception
except Exception:
    # probably on un-bundled version so try loading from local .env file
    secrets = dotenv_values('.env')

DASH_XML_KEY = 'LAWCHECKER_ADDED_NAMES_DASH_XML'
DASH_XML_URL = ''

# if no .env file error
try:
    DASH_XML_URL = secrets[DASH_XML_KEY]
except KeyError:
    # TODO: Log this
    logger.info(
        'Error: Either no .env file or the file does not have '
        f' {DASH_XML_KEY} environment variable set.'
        '\nPlease create a .env file in the root of the project'
        ' see .env.example for an example of the required format.'
    )


# ---------------------- default files and paths --------------------- #
DEFAULT_OUTPUT_NAME = 'Added_Names_Report.html'


XSLT_MARSHAL_PARAM_NAME = 'marsh-path'

XSL_1_NAME = 'anr_spo_rest.py'
XSL_2_NAME = 'anr_post_processing_html.py'
AN_HTML_TEMPLATE = 'anr_template.html'
COMPARE_REPORT_TEMPLATE_NAME = 'compare_report_template.html'
TEMPLATES_FOLDER = 'templates'

XML_FOLDER = 'Amendment_Paper_XML'
DASHBOARD_DATA_FOLDER = 'Dashboard_Data'

# path to folder containing the XSLT files
match RUNTIME_ENV:
    case RtEnv.EXE:
        PARENT_FOLDER = Path(sys.executable).parent
    case RtEnv.APP:
        PARENT_FOLDER = Path('../Resources')
    case _:
        # assume running as python script via usual interpreter
        # TODO: do we still need this?
        PARENT_FOLDER = Path(__file__).parent
        if not PARENT_FOLDER.joinpath('templates').exists():
            PARENT_FOLDER = PARENT_FOLDER.parent


REPORTS_FOLDER = (
    Path.home() / 'UK Parliament' / 'PPU - Scripts' / 'added_names_report' / '_Reports'
)

if RUNTIME_ENV == RtEnv.SCRIPT or not REPORTS_FOLDER.exists():
    # if running as a script or the REPORTS_FOLDER does not exist
    REPORTS_FOLDER = PARENT_FOLDER / '_Reports'


def get_template_path(template_name: str) -> Path:
    """Get template path that works in all environments."""
    try:
        # Try using importlib.resources first (works in all environments)
        template_files = files('lawchecker.templates')
        msg = f'Template files path: {template_files}'
        logger.info(msg)
        print(msg)
        return Path(str(template_files / template_name))
    except Exception:
        msg = 'Could not load template using importlib.resources'
        logger.info(msg)
        print(msg)
        # Fallback
        return PARENT_FOLDER / TEMPLATES_FOLDER / template_name


HTML_TEMPLATE = get_template_path(AN_HTML_TEMPLATE)

COMPARE_REPORT_TEMPLATE = get_template_path(COMPARE_REPORT_TEMPLATE_NAME)

print(f'HTML_TEMPLATE: {HTML_TEMPLATE}')
print(f'COMPARE_REPORT_TEMPLATE: {COMPARE_REPORT_TEMPLATE}')

if not COMPARE_REPORT_TEMPLATE.exists():
    COMPARE_REPORT_TEMPLATE = PARENT_FOLDER.parent.parent.joinpath(
        TEMPLATES_FOLDER, COMPARE_REPORT_TEMPLATE_NAME
    )


class GLOBAL_VARS:
    anr_working_folder: Path | None = None


# TODO: consider putting these in a class?
AMENDMENTS_URL_TEMPLATE = 'https://bills-api.parliament.uk/api/v1/Bills/{bill_id}/Stages/{stage_id}/Amendments?take=40&skip={skip}'

AMENDMENT_DETAILS_URL_TEMPLATE = 'https://bills-api.parliament.uk/api/v1/Bills/{bill_id}/Stages/{stage_id}/Amendments/{amendmet_id}'


# ------------------------- default xml stuff ------------------------ #

XMLNS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'  # akn is default ns
UKL = 'https://www.legislation.gov.uk/namespaces/UK-AKN'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'

NSMAP: dict[str, str] = {'xmlns': XMLNS, 'ukl': UKL, 'xsi': XSI}

# empty prefix [i.e. key=""] is allowed in some lxml
# methods/functions but not others. E.g. it's allowed in
# find but not allowed in xpath
NSMAP2 = NSMAP.copy()
NSMAP2[''] = XMLNS

PARSER = etree.XMLParser(remove_pis=True, remove_comments=True)
