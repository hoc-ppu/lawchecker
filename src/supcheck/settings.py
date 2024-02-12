import sys
from pathlib import Path

from lxml import etree

# ---------------------- default files and paths --------------------- #
DEFAULT_OUTPUT_NAME = "Added_Names_Report.html"


XSLT_MARSHAL_PARAM_NAME = "marsh-path"

XSL_1_NAME = "added-names-spo-rest.xsl"
XSL_2_NAME = "post-processing-html.xsl"

XML_FOLDER = "Amendment_Paper_XML"
DASHBOARD_DATA_FOLDER = "Dashboard_Data"

# path to folder containing the XSLT files
if hasattr(sys, "executable") and hasattr(sys, "_MEIPASS"):
    # we are using the bundled app
    PARENT_FOLDER = Path(sys.executable).parent
else:
    # assume running as python script via usual interpreter
    PARENT_FOLDER = Path(__file__).parent.parent
    if not PARENT_FOLDER.joinpath("XSLT").exists():
        PARENT_FOLDER = PARENT_FOLDER.parent

XSL_FOLDER = PARENT_FOLDER / "XSLT"

REPORTS_FOLDER = PARENT_FOLDER / "_Reports"

XSL_1_PATH = XSL_FOLDER / XSL_1_NAME
XSL_2_PATH = XSL_FOLDER / XSL_2_NAME

COMPARE_REPORT_TEMPLATE = PARENT_FOLDER.joinpath("compare_report_template.html")

ANR_WORKING_FOLDER: Path | None = None


DASH_XML_URL = (
    "https://hopuk.sharepoint.com/sites/bct-ppu/_api/web/lists/"
    "GetByTitle('Added%20Names')/items?$filter=Checked_x003f_%20eq%20%27false%27"
)


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
