import sys
from pathlib import Path

from dotenv import dotenv_values
from lxml import etree

try:
    # on the bundled app we expect the /env file to be in the temp folder
    bundled_env = Path(sys._MEIPASS).joinpath(".env")  # type: ignore
    if bundled_env.exists():
        secrets = dotenv_values(bundled_env)
    else:
        raise Exception
except Exception:
    # probably on un-bundled version so try loading from local .env file
    secrets = dotenv_values(".env")

DASH_XML_KEY = "LAWCHECKER_ADDED_NAMES_DASH_XML"
DASH_XML_URL = ""

# if no .env file error
try:
    DASH_XML_URL = secrets[DASH_XML_KEY]
except KeyError:
    # TODO: Log this
    print(
        "Error: Either no .env file or the file does not have "
        f" {DASH_XML_KEY} environment variable set."
        "\nPlease create a .env file in the root of the project"
        " see .env.example for an example of the required format."
    )


# ---------------------- default files and paths --------------------- #
DEFAULT_OUTPUT_NAME = "Added_Names_Report.html"


XSLT_MARSHAL_PARAM_NAME = "marsh-path"

XSL_1_NAME = "anr_spo_rest.py"
XSL_2_NAME = "anr_post_processing_html.py"
AN_HTML_TEMPLATE = "anr_template.html"
COMPARE_REPORT_TEMPLATE_NAME = "compare_report_template.html"
TEMPLATES_FOLDER = "templates"

XML_FOLDER = "Amendment_Paper_XML"
DASHBOARD_DATA_FOLDER = "Dashboard_Data"

# path to folder containing the XSLT files
if hasattr(sys, "executable") and hasattr(sys, "_MEIPASS"):
    # we are using the bundled app
    PARENT_FOLDER = Path(sys.executable).parent
else:
    # assume running as python script via usual interpreter
    # TODO: do we still need this?
    PARENT_FOLDER = Path(__file__).parent.parent
    if not PARENT_FOLDER.joinpath("template").exists():
        PARENT_FOLDER = PARENT_FOLDER.parent

XSL_FOLDER = PARENT_FOLDER / "src" / "lawchecker"

REPORTS_FOLDER = PARENT_FOLDER / "_Reports"

XSL_1_PATH = XSL_FOLDER / XSL_1_NAME
XSL_2_PATH = XSL_FOLDER / XSL_2_NAME
HTML_TEMPLATE = PARENT_FOLDER / TEMPLATES_FOLDER / AN_HTML_TEMPLATE

COMPARE_REPORT_TEMPLATE = PARENT_FOLDER.joinpath(
    TEMPLATES_FOLDER, COMPARE_REPORT_TEMPLATE_NAME
)

if not COMPARE_REPORT_TEMPLATE.exists():
    COMPARE_REPORT_TEMPLATE = PARENT_FOLDER.parent.parent.joinpath(
        TEMPLATES_FOLDER, COMPARE_REPORT_TEMPLATE_NAME
    )

ANR_WORKING_FOLDER: Path | None = None


# ------------------------- default xml stuff ------------------------ #

XMLNS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"  # akn is default ns
UKL = "https://www.legislation.gov.uk/namespaces/UK-AKN"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP: dict[str, str] = {"xmlns": XMLNS, "ukl": UKL, "xsi": XSI}

# empty prefix [i.e. key=""] is allowed in some lxml
# methods/functions but not others. E.g. it's allowed in
# find but not allowed in xpath
NSMAP2 = NSMAP.copy()
NSMAP2[""] = XMLNS

PARSER = etree.XMLParser(remove_pis=True, remove_comments=True)
