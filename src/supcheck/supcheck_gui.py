#!/usr/bin/env python3

import sys
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QMessageBox

from supcheck.supcheck_logger import logger  # must be before submodules...
from supcheck import added_names_report, settings
from supcheck.compare_amendment_documents import Report
from supcheck.compare_bill_documents import Report as BillReport
from supcheck.compare_bill_documents import diff_in_vscode
from supcheck.settings import ANR_WORKING_FOLDER, NSMAP
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
                # pass

            self.dash_xml_file = ""  # will be the xml file path
            self.lm_xml_folder = ""  # will be the lm xml folder path

            # LawMaker XML amendment files for the amenmet compare compare
            self.lm_new_xml_file = ""
            self.lm_old_xml_file = ""

            # LawMaker XML bill files for the bill compare
            self.new_bill_xml_file = ""
            self.old_bill_xml_file = ""

            self.workingFolderDateEdit.setDate(QtCore.QDate.currentDate())
            self.createWorkingFolderBtn.clicked.connect(self.anr_create_working_folder)

            self.openBrowser_btn.clicked.connect(self.open_dash_xml_in_browser)

            self.xmlFile_btn.clicked.connect(self.open_dash_xml_file)

            self.fm_xml_btn.clicked.connect(self.anr_open_amd_xml_dir)

            self.run_btn.clicked.connect(self.anr_run_xslts)

            # tab 2. compare amendments tab
            self.old_compare_XML_btn.clicked.connect(self.amd_open_old_xml)
            self.new_compare_XML_btn.clicked.connect(self.amd_open_new_xml)
            self.create_compare_btn.clicked.connect(self.amd_create_compare)
            self.create_compare_btn.setFocus()  # focus this button

            self.dated_folder_Path: Path | None = None

            # tab 3. compare bills tab
            self.new_bill_XML_btn.clicked.connect(self.bill_open_new_xml)
            self.old_bill_XML_btn.clicked.connect(self.bill_open_old_xml)
            self.create_bill_compare_btn.clicked.connect(self.bill_create_compare)

        def anr_create_working_folder(self):
            date_obj: datetime = self.workingFolderDateEdit.date().toPython()  # type: ignore
            formatted_date = date_obj.strftime("%Y-%m-%d")

            try:
                self.dated_folder_Path = settings.REPORTS_FOLDER.joinpath(formatted_date)
                self.dated_folder_Path.mkdir(parents=True, exist_ok=True)
                QMessageBox.information(
                    window, "Info", f"Working folder is:  {self.dated_folder_Path}"
                )

                global ANR_WORKING_FOLDER
                ANR_WORKING_FOLDER = self.dated_folder_Path

                # create subfolders for dashboard XML (and intermediate)
                # as well as lawmaker/framemaker XML
                anr_lawmaker_xml = self.dated_folder_Path.joinpath(settings.XML_FOLDER)
                anr_lawmaker_xml.mkdir(parents=True, exist_ok=True)
                dashboard_data = self.dated_folder_Path.joinpath(settings.DASHBOARD_DATA_FOLDER)
                dashboard_data.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QMessageBox.critical(
                    window, "Error", f"Could not create folder {repr(e)}"
                )

        def open_dash_xml_in_browser(self):
            """
            Load the dashboard XML in the default web browser.

            The user must download this first as there is security
            so we cant request it directly
            """
            webbrowser.open(settings.DASH_XML_URL)

        def open_dash_xml_file(self):
            default_location = settings.PARENT_FOLDER  # if user did not create working folder
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path / settings.DASHBOARD_DATA_FOLDER

            self.dash_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open dashboard data file", str(default_location)
            )

        def anr_open_amd_xml_dir(self):
            default_location = settings.PARENT_FOLDER
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path

            self.lm_xml_folder = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Folder", str(default_location)
            )

        def amd_open_old_xml(self):
            """Open the old amendment XML file.

            This is for the comparing the amendment paper the user is working
            on with the previous version. The Old XML file is the previous
            version."""

            default_location = settings.PARENT_FOLDER

            self.lm_old_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location), "XML files (*.xml)"
            )

        def amd_open_new_xml(self):
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

        def bill_open_old_xml(self):
            """
            Open the new bill XML file.
            """

            default_location = settings.PARENT_FOLDER

            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path

            self.old_bill_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open old XML file", str(default_location), "XML files (*.xml)"
            )

        def bill_open_new_xml(self):
            """
            Open the new bill XML file.
            """

            default_location = settings.PARENT_FOLDER

            old_bill_Path = Path(self.old_bill_xml_file)
            if old_bill_Path.exists() and old_bill_Path.is_file():
                default_location = old_bill_Path.parent

            self.new_bill_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open new XML file", str(default_location), "XML files (*.xml)"
            )

        def anr_run_xslts(self):
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
                    QMessageBox.critical(window, "Error", str(e))
                    print(traceback.print_exc(file=sys.stdout))
            else:
                print("No XML file selected.")

        def amd_create_compare(self):
            """
            Create a report comparing the old and new amendment XML files.
            """

            # Check that Old and New XML fields have been populated

            if not self.lm_old_xml_file:
                QMessageBox.critical(
                    window, "Error", "No old XML file selected."
                )
                return

            if not self.lm_new_xml_file:
                QMessageBox.critical(
                    window, "Error", "No new XML file selected."
                )
                return

            old_xml_path = Path(self.lm_old_xml_file).resolve()
            new_xml_path = Path(self.lm_new_xml_file).resolve()


            # Check the Old and New XML files can both be parsed as XML

            old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
            new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

            if not old_xml:
                QMessageBox.critical(
                    window, "Error", f"Old XML file is not valid XML: {old_xml_path}"
                )
                return

            if not new_xml:
                QMessageBox.critical(
                    window, "Error", f"New XML file is not valid XML: {new_xml_path}"
                )
                return


            # Check that the  <FRBRalias name="alternateUri" />
            # element in both the Old and New XML is the same

            old_xml_uri = old_xml.find(
                "//xmlns:FRBRWork/xmlns:FRBRalias[@name='alternateUri']",
                namespaces=NSMAP,
            )
            new_xml_uri = new_xml.find(
                "//xmlns:FRBRWork/xmlns:FRBRalias[@name='alternateUri']",
                namespaces=NSMAP,
            )

            if old_xml_uri is not None and new_xml_uri is not None:
                if old_xml_uri.attrib["value"] != new_xml_uri.attrib["value"]:
                    QMessageBox.critical(
                        window, "Error", "XML files do not represent the same bill"
                    )
                    return


            # Check that the date in the  <FRBRdate date="published" />
            # element in the New XML is more recent than the date in the Old XML
            xpath = "//xmlns:FRBRWork/xmlns:FRBRdate[@name='published']"
            old_xml_date = old_xml.find(xpath, namespaces=NSMAP)
            new_xml_date = new_xml.find(xpath, namespaces=NSMAP)

            if old_xml_date is not None and new_xml_date is not None:
                old_xml_date_obj = datetime.strptime(
                    old_xml_date.attrib["date"], "%Y-%m-%d"
                )
                new_xml_date_obj = datetime.strptime(
                    new_xml_date.attrib["date"], "%Y-%m-%d"
                )

                if not (old_xml_date_obj < new_xml_date_obj):
                    QMessageBox.critical(
                        window,
                        "Error",
                        "New XML must be dated more recently than Old XML",
                    )
                    return

            if ANR_WORKING_FOLDER is None:
                dated_folder_Path = settings.REPORTS_FOLDER.joinpath(
                    datetime.now().strftime("%Y-%m-%d")
                ).resolve()
            else:
                dated_folder_Path = (
                    ANR_WORKING_FOLDER.resolve()
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

        def bill_create_compare(self):
            """
            Create the compare report for bills
            """

            if not self.old_bill_xml_file:
                QMessageBox.critical(
                    window, "Error", "No old XML file selected."
                )
                return

            if not self.new_bill_xml_file:
                QMessageBox.critical(
                    window, "Error", "No new XML file selected."
                )
                return

            old_xml_path = Path(self.old_bill_xml_file).resolve()
            new_xml_path = Path(self.new_bill_xml_file).resolve()

            # Check the Old and New XML files can both be parsed as XML

            old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
            new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

            print()

            if not old_xml:
                QMessageBox.critical(
                    window, "Error", f"Old XML file is not valid XML: {old_xml_path}"
                )
                return

            if not new_xml:
                QMessageBox.critical(
                    window, "Error", f"New XML file is not valid XML: {new_xml_path}"
                )
                return


            out_html_Path = old_xml_path.parent.joinpath("Compare_Bills.html")

            # checked status of checkbox
            vs_code_diff: bool = self.vs_code_diff.isChecked()

            report = BillReport(
                old_xml_path,
                new_xml_path,
            )
            report.html_tree.write(
                str(out_html_Path),
                encoding="utf-8",
                doctype="<!DOCTYPE html>"
            )

            webbrowser.open(out_html_Path.resolve().as_uri())

            if vs_code_diff:
                diff_in_vscode(report.old_doc.root, report.new_doc.root)


    # use gui version
    app = QtWidgets.QApplication(args)

    # window = QtWidgets.QMainWindow()
    window = MainWindow()
    window.show()

    # import logging
    # for logger_name, lgr in logging.root.manager.loggerDict.items():
    #     print(f"{logger_name=}, {lgr=}")
    #     print("   ", lgr.handlers)

    app.exec()


if __name__ == "__main__":
    main()
