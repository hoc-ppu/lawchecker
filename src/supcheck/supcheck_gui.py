#!/usr/bin/env python3

import sys
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from supcheck.supcheck_logger import logger  # must be before anything from submodules
from supcheck import added_names_report, settings
from supcheck.compare_amendment_documents import Report
from supcheck.settings import NSMAP, WORKING_FOLDER
from supcheck.submodules.python_toolbox import pp_xml_lxml
from supcheck.ui.addedNames import Ui_MainWindow


def main():

    args = sys.argv


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

            self.run_btn.clicked.connect(self.run_xslts)

            # tab 2. compare tab
            self.old_compare_XML_btn.clicked.connect(self.open_old_amd_xml)
            self.new_compare_XML_btn.clicked.connect(self.open_new_amd_xml)
            self.create_compare_btn.clicked.connect(self.create_compare)
            self.create_compare_btn.setFocus()  # focus this button

            self.dated_folder_Path: Path | None = None

        def create_working_folder(self):
            date_obj: datetime = self.workingFolderDateEdit.date().toPython()  # type: ignore
            formatted_date = date_obj.strftime("%Y-%m-%d")

            try:
                self.dated_folder_Path = settings.REPORTS_FOLDER.joinpath(formatted_date)
                self.dated_folder_Path.mkdir(parents=True, exist_ok=True)
                QtWidgets.QMessageBox.information(
                    window, "Info", f"Working folder is:  {self.dated_folder_Path}"
                )

                global WORKING_FOLDER
                WORKING_FOLDER = self.dated_folder_Path

                # create subfolders for dashboard XML (and intermediate)
                # as well as lawmaker/framemaker XML
                lawmaker_xml = self.dated_folder_Path.joinpath(settings.XML_FOLDER)
                lawmaker_xml.mkdir(parents=True, exist_ok=True)
                dashboard_data = self.dated_folder_Path.joinpath(settings.DASHBOARD_DATA_FOLDER)
                dashboard_data.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    window, "Error", f"Could not create folder {repr(e)}"
                )

        def open_browser(self):
            webbrowser.open(settings.DASH_XML_URL)

        def open_dash_xml_file(self):
            default_location = settings.PARENT_FOLDER  # if user did not create working folder
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path / settings.DASHBOARD_DATA_FOLDER

            self.dash_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open dashboard data file", str(default_location)
            )

        def open_amd_xml_dir(self):
            default_location = settings.PARENT_FOLDER
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

            default_location = settings.PARENT_FOLDER

            self.lm_old_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location), "XML files (*.xml)"
            )

        def open_new_amd_xml(self):
            """Open the old amendment XML file.

            This is for the comparing the amendment paper the user is working
            on with the previous version. The Old XML file is the previous
            version."""

            default_location = settings.PARENT_FOLDER

            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path

            self.lm_new_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location), "XML files (*.xml)"
            )

        def run_xslts(self):
            lm_xml_folder_Path: Path | None = None

            if self.lm_xml_folder:
                lm_xml_folder_Path = Path(self.lm_xml_folder)

            if self.dash_xml_file and Path(self.dash_xml_file).resolve().exists():
                xsl_1_Path = settings.XSL_1_PATH
                xsl_2_Path = settings.XSL_2_PATH
                input_Path = Path(self.dash_xml_file).resolve()
                try:
                    added_names_report.run_xslts(
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
                dated_folder_Path = settings.REPORTS_FOLDER.joinpath(
                    datetime.now().strftime("%Y-%m-%d")
                ).resolve()
            else:
                dated_folder_Path = (
                    WORKING_FOLDER.resolve()
                )  # working folder selected in UI
            dated_folder_Path.mkdir(parents=True, exist_ok=True)

            xml_folder_Path = dated_folder_Path.joinpath(settings.DASHBOARD_DATA_FOLDER)
            xml_folder_Path.mkdir(parents=True, exist_ok=True)

            out_html_Path = dated_folder_Path.joinpath("Compare_Report.html")

            # checked status of checkbox
            days_between_papers: bool = self.days_between_chk.isChecked()

            report = Report(
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


if __name__ == "__main__":
    main()
