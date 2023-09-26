#!/usr/bin/env python3

import re
import sys
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

# 3rd party saxon imports
import saxonche
import submodules.python_toolbox.pp_xml_lxml as pp_xml_lxml

import check_amendments

USE_GUI = True

# --- conditional imports ---
if len(sys.argv) > 1:
    USE_GUI = False
    # comand line only imports
    import argparse
else:
    # GUI only imports
    from PySide6 import QtCore, QtWidgets
    from ui.addedNames import Ui_MainWindow

DEFAULT_OUTPUT_FILE_NAME = "Added_Names_Report.html"

XMLNS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"  # akn is default ns

NSMAP: dict[str, str] = {"dns": XMLNS}

XSLT_MARSHAL_PARAM_NAME = "marsh-path"

DASH_XML_URL = (
    "***REMOVED***"
    "***REMOVED***"
)

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
    PARENT_FOLDER = Path(__file__).parent
    if not PARENT_FOLDER.joinpath("XSLT").exists():
        PARENT_FOLDER = PARENT_FOLDER.parent

XSL_FOLDER = PARENT_FOLDER / "XSLT"

REPORTS_FOLDER = PARENT_FOLDER / "_Reports"

XSL_1_PATH = XSL_FOLDER / XSL_1_NAME
XSL_2_PATH = XSL_FOLDER / XSL_2_NAME

WORKING_FOLDER: Optional[Path] = None


def main():
    cli_args = sys.argv
    if USE_GUI:
        gui(cli_args)  # graphical version
    else:
        cli(cli_args)  # command line version


def cli(cli_args):
    # do cmd line version

    def _dir_path(path):
        # get directory
        if Path(path).is_dir():
            return path
        else:
            raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

    parser = argparse.ArgumentParser(
        description=(
            "Create an HTML report of added names from XML downloaded form the"
            " Dashboard"
        )
    )

    parser.add_argument(
        "file",
        metavar="XML File",
        type=open,
        help=(
            "File path to the XML you wish to process. Use quotes if there are spaces."
        ),
    )

    parser.add_argument(
        "--xslts",
        metavar="XSLT Folder",
        type=_dir_path,
        help=(
            "Path to the folder containing the XSLTs wish to run. "
            "Use quotes if there are spaces."
        ),
    )

    parser.add_argument(
        "--marshal-dir",
        metavar="XML Folder",
        type=_dir_path,
        help="Optional Path to the folder containing the XML files "
        "(from LawMaker or FrameMaker) that you wish to use to marshal "
        "the report. Use quotes if there are spaces.",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file name",
        default=DEFAULT_OUTPUT_FILE_NAME,
    )

    args = parser.parse_args(cli_args[1:])
    print(args)

    input_Path = Path(args.file.name)

    if args.xslts:
        xsl_1_Path = Path(args.xslts) / XSL_1_NAME
        xsl_2_Path = Path(args.xslts) / XSL_2_NAME
    else:
        xsl_1_Path = XSL_1_PATH
        xsl_2_Path = XSL_2_PATH

    if args.marshal_dir:
        marshal_dir = Path(args.marshal_dir)
    else:
        marshal_dir = None

    print(f"marshal_dir={marshal_dir}")
    run_xslts(
        input_Path,
        xsl_1_Path,
        xsl_2_Path,
        parameter=marshal_dir,
        output_file_name=args.output
    )


def gui(args):
    class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
        def __init__(self, *args, obj=None, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.setupUi(self)

            if sys.platform == "darwin":
                # annoyingly sizing works differently on macOS and windows
                self.resize(self.size().width(), 740)  # fit widgets on mac

            self.dash_xml_file = ""  # will be the xml file path
            self.lm_xml_folder = ""  # will be the lm xml folder path

            self.lm_new_xml_file = ""  # the new LM XML file for the compare
            self.lm_old_xml_file = ""  # the old LM XML file for the compare

            self.workingFolderDateEdit.setDate(QtCore.QDate.currentDate())
            self.createWorkingFolderBtn.clicked.connect(self.create_working_folder)

            self.openBrowser_btn.clicked.connect(self.open_browser)

            self.xmlFile_btn.clicked.connect(self.open_dash_xml_file)

            self.fm_xml_btn.clicked.connect(self.open_amd_xml_dir)

            self.run_btn.clicked.connect(self.run)

            # tab 2. compare tab
            self.old_compare_XML_btn.clicked.connect(self.open_old_amd_xml)
            self.new_compare_XML_btn.clicked.connect(self.open_new_amd_xml)
            self.create_compare_btn.clicked.connect(self.create_compare)
            self.create_compare_btn.setFocus()  # focus this button

            self.dated_folder_Path: Optional[Path] = None

        def create_working_folder(self):
            date_obj = self.workingFolderDateEdit.date().toPython()
            formatted_date = date_obj.strftime("%Y-%m-%d")

            try:
                self.dated_folder_Path = REPORTS_FOLDER.joinpath(formatted_date)
                self.dated_folder_Path.mkdir(parents=True, exist_ok=True)
                QtWidgets.QMessageBox.information(
                    window, "Info", f"Working folder is:  {self.dated_folder_Path}"
                )

                global WORKING_FOLDER
                WORKING_FOLDER = self.dated_folder_Path

                # create subfolders for dashboard XML (and intermediate)
                # as well as lawmaker/framemaker XML
                lawmaker_xml = self.dated_folder_Path.joinpath(XML_FOLDER)
                lawmaker_xml.mkdir(parents=True, exist_ok=True)
                dashboard_data = self.dated_folder_Path.joinpath(DASHBOARD_DATA_FOLDER)
                dashboard_data.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    window, "Error", f"Could not create folder {repr(e)}"
                )

        def open_browser(self):
            webbrowser.open(DASH_XML_URL)

        def open_dash_xml_file(self):
            default_location = PARENT_FOLDER  # if user did not create working folder
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path / DASHBOARD_DATA_FOLDER

            self.dash_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open dashboard data file", str(default_location)
            )

        def open_amd_xml_dir(self):
            default_location = PARENT_FOLDER
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path

            self.lm_xml_folder = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Folder", str(default_location)
            )

        def open_old_amd_xml(self):
            """Open the old amendment XML file.

            This is for the comparing the amendment paper the user is working
            on with the previous version. The Old XML file is the previous
            version."""

            default_location = PARENT_FOLDER

            self.lm_old_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location)
            )

        def open_new_amd_xml(self):
            """Open the old amendment XML file.

            This is for the comparing the amendment paper the user is working
            on with the previous version. The Old XML file is the previous
            version."""

            default_location = PARENT_FOLDER

            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path

            self.lm_new_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location)
            )

        def run(self):
            lm_xml_folder_Path: Optional[Path] = None

            if self.lm_xml_folder:
                lm_xml_folder_Path = Path(self.lm_xml_folder)

            if self.dash_xml_file and Path(self.dash_xml_file).resolve().exists():
                xsl_1_Path = XSL_1_PATH
                xsl_2_Path = XSL_2_PATH
                input_Path = Path(self.dash_xml_file).resolve()
                try:
                    run_xslts(
                        input_Path, xsl_1_Path, xsl_2_Path, parameter=lm_xml_folder_Path
                    )
                except Exception as e:
                    QtWidgets.QMessageBox.critical(window, "Error", str(e))
                    print(traceback.print_exc(file=sys.stdout))
            else:
                print("No XML file selected.")

        def create_compare(self):
            """
            Create the compare report
            """


            # Check that Old and New XML fields have been populated

            if not self.lm_old_xml_file:
                QtWidgets.QMessageBox.critical(
                    window, "Error", "No old XML file selected."
                )
                return

            if not self.lm_new_xml_file:
                QtWidgets.QMessageBox.critical(
                    window, "Error", "No new XML file selected."
                )
                return

            old_xml_path = Path(self.lm_old_xml_file).resolve()
            new_xml_path = Path(self.lm_new_xml_file).resolve()


            # Check the Old and New XML files can both be parsed as XML

            old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
            new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

            if not old_xml:
                QtWidgets.QMessageBox.critical(
                    window, "Error", f"Old XML file is not valid XML: {old_xml_path}"
                )
                return

            if not new_xml:
                QtWidgets.QMessageBox.critical(
                    window, "Error", f"New XML file is not valid XML: {new_xml_path}"
                )
                return


            # Check that the  <FRBRalias name="alternateUri" />
            # element in both the Old and New XML is the same

            old_xml_uri = old_xml.find(
                "//dns:FRBRWork/dns:FRBRalias[@name='alternateUri']",
                namespaces=NSMAP,
            )
            new_xml_uri = new_xml.find(
                "//dns:FRBRWork/dns:FRBRalias[@name='alternateUri']",
                namespaces=NSMAP,
            )

            if old_xml_uri is not None and new_xml_uri is not None:
                if old_xml_uri.attrib["value"] != new_xml_uri.attrib["value"]:
                    QtWidgets.QMessageBox.critical(
                        window, "Error", "XML files do not represent the same bill"
                    )
                    return


            # Check that the date in the  <FRBRdate date="published" />
            # element in the New XML is more recent than the date in the Old XML

            old_xml_date = old_xml.find(
                "//dns:FRBRWork/dns:FRBRdate[@name='published']",
                namespaces=NSMAP,
            )
            new_xml_date = new_xml.find(
                "//dns:FRBRWork/dns:FRBRdate[@name='published']",
                namespaces=NSMAP,
            )

            if old_xml_date is not None and new_xml_date is not None:
                old_xml_date_obj = datetime.strptime(
                    old_xml_date.attrib["date"], "%Y-%m-%d"
                )
                new_xml_date_obj = datetime.strptime(
                    new_xml_date.attrib["date"], "%Y-%m-%d"
                )

                if not (old_xml_date_obj < new_xml_date_obj):
                    QtWidgets.QMessageBox.critical(
                        window,
                        "Error",
                        "New XML must be dated more recently than Old XML",
                    )
                    return

            if WORKING_FOLDER is None:
                dated_folder_Path = REPORTS_FOLDER.joinpath(
                    datetime.now().strftime("%Y-%m-%d")
                ).resolve()
            else:
                dated_folder_Path = (
                    WORKING_FOLDER.resolve()
                )  # working folder selected in UI
            dated_folder_Path.mkdir(parents=True, exist_ok=True)

            xml_folder_Path = dated_folder_Path.joinpath(DASHBOARD_DATA_FOLDER)
            xml_folder_Path.mkdir(parents=True, exist_ok=True)

            out_html_Path = dated_folder_Path.joinpath("Compare_Report.html")

            # checked status of checkbox
            days_between_papers: bool = self.days_between_chk.isChecked()

            report = check_amendments.Report(
                old_xml_path,
                new_xml_path,
                days_between_papers=days_between_papers
            )
            report.html_tree.write(
                str(out_html_Path),
                encoding="utf-8",
                doctype="<!DOCTYPE html>"
            )

            webbrowser.open(out_html_Path.resolve().as_uri())


    # use gui version
    app = QtWidgets.QApplication(args)

    # window = QtWidgets.QMainWindow()
    window = MainWindow()
    window.show()

    app.exec()


def remove_docstring(parameter: Path):
    """Process FM XML files to remove docstring and overwrite original"""

    # lets also turn it into an absolute path
    parameter_abs = parameter.resolve()

    # get all xml files in folder
    fm_xml_files = list(parameter_abs.glob("*.xml"))

    # loop through XML files and remove the doctypes
    for file in fm_xml_files:

        LM_XML = False
        root_start = 0
        file_lines = []

        with open(file, "r", encoding="utf-8") as f:
            file_lines = f.readlines()

            for i, line in enumerate(file_lines):
                if "<akomaNtoso" in line:
                    # if LawMaker XML we expect the root to be akomaNtoso
                    # in which case completely ignore
                    LM_XML = True
                    break
                if re.search(r"<[A-Za-z0-9._]", line):
                    # found root
                    root_start = i
                    break

        if LM_XML:
            # do not do anything to LM XML
            continue

        print(f"Trying to remove docstring from {file.name}")

        # try to overwrite file
        with open(file, "w", encoding="UTF-8") as fi:
            # need to remove FM doctype
            # remove anything before the root element
            fi.writelines(file_lines[root_start:])


def extract_date(input_Path: Path) -> str:
    """Extract date form input XML from SharePoint"""

    with open(input_Path) as f:
        input_xml_str = f.read()

    # print(f'input_xml_str length is: {len(input_xml_str)}')
    # get the updated date
    match = re.search(r"(<updated>)([A-Z0-9:+-]+)(</updated>)", input_xml_str)
    date_str = ""
    if match:
        date_str = match.group(2)
        print(f"Date extracted from input xml (from SharePoint) {date_str}")

    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        formated_date = dt.strftime("%Y-%m-%d__%H-%M")
    except Exception as e:
        print(repr(e))
        formated_date = ""

    return formated_date


def check_xsl_paths(*xsls: Path) -> bool:
    for xsl_Path in xsls:
        try:
            # check xsl paths are valid
            xsl_Path = xsl_Path.resolve(strict=True)

        except FileNotFoundError as e:
            err_txt = (
                "The following required XSLT file is missing:"
                f"\n\n{xsl_Path}"
                "\n\nUsually you should have two XSL files in a folder called 'XSLT'"
                " and that folder should be in the same folder as this program."
            )
            print("Error:", err_txt)
            if USE_GUI:
                # this can be caught in the GUI code and the
                # Error message displayed in a GUI window
                raise Exception(err_txt) from e
            return False

    return True


def run_xslts(
    input_Path: Path,
    xsl_1_Path: Path,
    xsl_2_Path: Path,
    parameter: Optional[Path] = None,
    output_file_name: str = DEFAULT_OUTPUT_FILE_NAME,
):
    print(f"{input_Path=}\n{xsl_1_Path=}\n{xsl_2_Path=}\n{parameter=}")

    xsls_exist = check_xsl_paths(xsl_1_Path, xsl_2_Path)
    if not xsls_exist:
        return

    formated_date = extract_date(input_Path)

    intermediate_file_name = f"{formated_date}_intermediate.xml"
    input_file_resave_name = f"{formated_date}_input_from_SP.xml"

    if WORKING_FOLDER is None:
        dated_folder_Path = REPORTS_FOLDER.joinpath(formated_date).resolve()
    else:
        dated_folder_Path = WORKING_FOLDER.resolve()  # working folder selected in UI
    dated_folder_Path.mkdir(parents=True, exist_ok=True)

    xml_folder_Path = dated_folder_Path.joinpath(DASHBOARD_DATA_FOLDER)
    xml_folder_Path.mkdir(parents=True, exist_ok=True)

    intermidiate_Path = xml_folder_Path.joinpath(intermediate_file_name)
    out_html_Path = dated_folder_Path.joinpath(output_file_name)

    print(f"{intermidiate_Path=}")
    print(f"{out_html_Path=}")

    # resave the input file
    resave_Path = xml_folder_Path.joinpath(input_file_resave_name)
    with open(resave_Path, "w") as f:
        f.write(input_Path.read_text())

    with saxonche.PySaxonProcessor(license=False) as proc:
        # print(proc.version)

        # need to be as uri in case there are spaces in the path
        input_path = input_Path.resolve().as_uri()
        intermidiate_path = intermidiate_Path.resolve().as_uri()
        outfilepath = out_html_Path.resolve().as_uri()

        # --- 1st XSLT ---
        xsltproc = proc.new_xslt30_processor()

        executable = xsltproc.compile_stylesheet(stylesheet_file=str(xsl_1_Path))
        executable.transform_to_file(
            source_file=input_path, output_file=intermidiate_path
        )

        # --- 2nd XSLT ---
        xsltproc2 = proc.new_xslt30_processor()

        executable2 = xsltproc2.compile_stylesheet(stylesheet_file=str(xsl_2_Path))

        if parameter:
            # get path to folder containing LM/FM XML file(s) and pass this to
            # the XSLT processor as a parameter. This is for marshelling.
            remove_docstring(parameter)
            parameter_str = parameter.resolve().as_uri()  # uri works best with Saxon
            param = proc.make_string_value(parameter_str)

            executable2.set_parameter(XSLT_MARSHAL_PARAM_NAME, param)

        executable2.transform_to_file(
            source_file=intermidiate_path, output_file=outfilepath
        )

        # --- finished transforms ---

        print(f"Created: {out_html_Path}")

        webbrowser.open(outfilepath)

        print("Done.")


if __name__ == "__main__":
    main()
