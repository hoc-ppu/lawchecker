import io
import logging
import os
import platform
import subprocess
import sys
import time
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import cast

import requests
import webview
from webview import Window  # TODO: fix this

from lawchecker import added_names_report, pp_xml_lxml, settings
from lawchecker.compare_amendment_documents import Report
from lawchecker.compare_bill_documents import Report as BillReport
from lawchecker.compare_bill_documents import diff_in_vscode
from lawchecker.compare_bill_numbering import CompareBillNumbering
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import ANR_WORKING_FOLDER
from lawchecker.ui_feedback import ProgressModal, UILogHandler

APP_FROZEN = getattr(sys, 'frozen', False)

# Reference to the active window will be stored here
window: Window | None = None

# add modal to the logger

def set_version_info(window_local: Window | None = None):

    logger.info(f"{window_local=}")
    if not window_local:
        window_local = window

    match settings.RUNTIME_ENV:
        case settings.RtEnv.EXE:
            version_path = Path(sys._MEIPASS, "VERSION")  # type: ignore
        case settings.RtEnv.APP:
            version_path = Path("../Resources/VERSION")
        case _:
            version_path = Path("VERSION")

    version_str = "No version str"
    try:
        with open("VERSION") as version_path:
            version_str = version_path.read().strip()
    except Exception:
        pass

    logger.info(f"{version_str=}")

    # window_local.evaluate_js(f"updateVersionInfo('{version_str}')")
    window_local.evaluate_js(f"window.pywebview.state.setVersionInfo(\"{version_str}\")")


class Api:
    def __init__(self):
        self.com_bill_old_xml: Path | None = None
        self.com_bill_new_xml: Path | None = None

        self.com_compare_number_dir: Path | None = None

        self.dated_folder_Path: Path | None = None
        self.dash_xml_file: Path | None = None
        self.lm_xml_folder: Path | None = None

        self.com_amend_old_xml: Path | None = None
        self.com_amend_new_xml: Path | None = None


    def _open_file_dialog(self, file_type="") -> Path | None:

        # select a file

        active_window = webview.active_window()
        active_window = cast(Window, active_window)

        if file_type == "xml":
            file_types = ("XML files (*.xml)",)
        elif file_type == "html":
            file_types = ("HTML files (*.html)",)
        else:
            file_types = ("All files (*.*)",)

        result = active_window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types
        )

        if result is None:
            return None

        return Path(result[0])


    def open_file_dialog(self, file_specifier: str, file_type="") -> str:
        # select a file

        _file = self._open_file_dialog(file_type)

        match file_specifier:
            case "com_bill_old_xml":
                self.com_bill_old_xml = _file
            case "com_bill_new_xml":
                self.com_bill_new_xml = _file
            case "com_amend_old_xml":
                self.com_amend_old_xml = _file
            case "com_amend_new_xml":
                self.com_amend_new_xml = _file
            case _:
                print(f"Error: Unknown file specifier: {file_specifier}")

        return str(_file)

    def select_folder(self, folder_specifier: str) -> None:
        print(f"select_folder called with folder_specifier: {folder_specifier}")
        active_window = webview.active_window()
        active_window = cast(Window, active_window)

        result = active_window.create_file_dialog(
            webview.FOLDER_DIALOG, directory=str(Path.home())
        )

        if result is None:
            print("No folder selected.")
            return

        selected_folder = Path(result[0])
        print(f"Selected folder: {selected_folder}")

        match folder_specifier:
            case "compare_number_dir":
                self.com_compare_number_dir = selected_folder
                print(f"compare_number_dir set to: {self.com_compare_number_dir}")
            case _:
                print(f"Error: Unknown folder specifier: {folder_specifier}")

    def anr_create_working_folder(self, date_str: str) -> str:

        """
        Create a working folder for the Added Names Report.

        @Called from: AddedNamesCollapsible <Button text="Create working folder">

        """

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%Y-%m-%d")

            self.dated_folder_Path = settings.REPORTS_FOLDER.joinpath(formatted_date)
            self.dated_folder_Path.mkdir(parents=True, exist_ok=True)

            global ANR_WORKING_FOLDER
            ANR_WORKING_FOLDER = self.dated_folder_Path

            # create subfolders for dashboard XML (and intermediate)
            # as well as lawmaker/framemaker XML
            anr_lawmaker_xml = self.dated_folder_Path.joinpath(settings.XML_FOLDER)
            anr_lawmaker_xml.mkdir(parents=True, exist_ok=True)
            dashboard_data = self.dated_folder_Path.joinpath(settings.DASHBOARD_DATA_FOLDER)
            dashboard_data.mkdir(parents=True, exist_ok=True)

            return f"Working folder created: {self.dated_folder_Path}"
        except Exception as e:
            return f"Error: Could not create folder {repr(e)}"

    def open_folder(self, folder_path: str) -> str:

        """
        Open a folder in the default file manager.
        """

        try:
            if platform.system() == "Windows":
                os.startfile(folder_path)  # type: ignore
            elif platform.system() == "Darwin":
                # macOS
                subprocess.run(["open", folder_path])
            else:
                # Linux and other Unix-like systems
                subprocess.run(["xdg-open", folder_path])

            msg = f"Opened folder: {folder_path}"
            logger.info(msg)
            return msg

        except Exception as e:
            msg = f"Could not open folder {repr(e)}"
            logger.error(msg)
            return f"Error: {msg}"



    def open_dash_xml_in_browser(self) -> str:
        """
        Loads the Added Names dashboard XML in the default web browser.

        The user must download this first as there is security
        so we can't request it directly.
        """
        try:
            webbrowser.open(settings.DASH_XML_URL)  # type: ignore
            return "Dashboard XML opened in browser."
        except Exception as e:
            return f"Error: Could not open browser {repr(e)}"

    def open_dash_xml_file(self) -> str:
        """
        Opens a file dialog to select the dashboard XML file.
        """
        default_location = settings.PARENT_FOLDER  # if user did not create working folder
        if self.dated_folder_Path is not None:
            default_location = self.dated_folder_Path / settings.DASHBOARD_DATA_FOLDER

        active_window = webview.active_window()
        active_window = cast(Window, active_window)

        result = active_window.create_file_dialog(
            webview.OPEN_DIALOG, directory=str(default_location)
            # Allow all files instead of just XML. This is because when users
            # download the data from sharepoint it is saved as .txt. It is
            # easier for uses to be able to select the .txt file rather than
            # first having to change the file extension.
            # , file_types=("XML files (*.xml)",)
        )

        if result is None:
            return "No file selected."

        self.dash_xml_file = Path(result[0])
        return f"Selected file: {self.dash_xml_file}"

    def anr_open_amd_xml_dir(self) -> str:
        """
        Open a directory selection dialog to select the amendment XML directory.
        """
        default_location = settings.PARENT_FOLDER
        if self.dated_folder_Path is not None:
            default_location = self.dated_folder_Path

        active_window = webview.active_window()
        active_window = cast(Window, active_window)

        result = active_window.create_file_dialog(
            webview.FOLDER_DIALOG, directory=str(default_location)
        )

        if result is None:
            return "No directory selected."

        self.lm_xml_folder = Path(result[0])
        return f"Selected directory: {self.lm_xml_folder}"

    def anr_run_xslts(self) -> str:
        """
        Run the transforms  to create the Added Names report.
        """
        lm_xml_folder_Path: Path | None = None

        if self.lm_xml_folder:
            lm_xml_folder_Path = Path(self.lm_xml_folder)

        if not (self.dash_xml_file and Path(self.dash_xml_file).resolve().exists()):
            return "No XML file selected."

        input_Path = Path(self.dash_xml_file).resolve()

        try:
            with ProgressModal() as modal:
                modal.update(f"Dashboard XML: {self.dash_xml_file}")

                if self.lm_xml_folder:
                    modal.update(f"Marshal XML: {self.lm_xml_folder}")
                else:
                    modal.update("No marshal XML selected")

                modal.update("Running...")
                added_names_report.run_xslts(
                    input_Path, parameter=lm_xml_folder_Path
                )
                modal.update("Report ready.")

            return "Report created successfully."

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return f"Error: {str(e)}"


    def bill_create_html_compare(self):
        """
        Create the compare report for bills
        """

        # TODO: add better validation and error handling
        if not self.com_bill_old_xml:
            logger.error("No old XML file selected.")
            return

        if not self.com_bill_new_xml:
            logger.error("No new XML file selected.")
            return

        old_xml_path = Path(self.com_bill_old_xml).resolve()
        new_xml_path = Path(self.com_bill_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        # TODO: Improve the below
        if not old_xml:
            logger.error(f"Old XML file is not valid XML: {old_xml_path}")
            return

        if not new_xml:
            logger.error(f"New XML file is not valid XML: {new_xml_path}")
            return

        out_html_Path = old_xml_path.parent.joinpath("Compare_Bills.html")

        with ProgressModal() as modal:

            modal.update(f"Old XML path: {old_xml_path}")
            modal.update(f"New XML path: {new_xml_path}")

            report = BillReport(
                old_xml_path,
                new_xml_path,
            )
            report.html_tree.write(
                str(out_html_Path),
                method="html",
                encoding="utf-8",
                doctype="<!DOCTYPE html>"
            )
            modal.update(f"HTML report created: {out_html_Path}")
            modal.update("Attempting to open in browser...")

            webbrowser.open(out_html_Path.resolve().as_uri())

    def bill_compare_in_vs_code(self):

        if not self.com_bill_old_xml:
            logger.error("No old XML file selected.")
            return

        if not self.com_bill_new_xml:
            logger.error("No new XML file selected.")
            return

        old_xml_path = Path(self.com_bill_old_xml).resolve()
        new_xml_path = Path(self.com_bill_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        if not old_xml:
            logger.error(f"Old XML file is not valid XML: {old_xml_path}")
            return

        if not new_xml:
            logger.error(f"New XML file is not valid XML: {new_xml_path}")
            return

        report = BillReport(
            old_xml_path,
            new_xml_path,
        )

        diff_in_vscode(report.old_doc.root, report.new_doc.root)

    def compare_bill_numbering(self):
        """
        Executes the compare the numbering of bills
        """
        print("compare_bill_numbering called")

        if not self.com_compare_number_dir:
            print("Error: No directory selected.")
            return "Error: No directory selected."

        compare_dir = Path(self.com_compare_number_dir).resolve()
        print(f"compare_dir resolved to: {compare_dir}")

        if not compare_dir.is_dir():
            print("Error: Selected path is not a directory.")
            return "Error: Selected path is not a directory."

        compare = CompareBillNumbering.from_folder(compare_dir)
        print("CompareBillNumbering instance created")

        compare.save_csv(compare_dir)
        print("CSV files created")


    def amend_create_html_compare(
        self, days_between_papers=False
    ):
        """
        Create the compare report for amendments
        """

        # TODO: add better validation and error handling
        if not self.com_amend_old_xml:
            logger.error("No old XML file selected.")
            return

        if not self.com_amend_new_xml:
            logger.error("No new XML file selected.")
            return

        old_xml_path = Path(self.com_amend_old_xml).resolve()
        new_xml_path = Path(self.com_amend_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        print()

        # TODO: Improve the below
        if not old_xml:
            logger.error(f"Old XML file is not valid XML: {old_xml_path}")
            return

        if not new_xml:
            logger.error(f"New XML file is not valid XML: {new_xml_path}")
            return

        out_html_Path = old_xml_path.parent.joinpath("Compare_Amendments.html")

        report = Report(
            old_xml_path,
            new_xml_path,
            days_between_papers,
        )
        report.html_tree.write(
            str(out_html_Path),
            method="html",
            encoding="utf-8",
            doctype="<!DOCTYPE html>"
        )

        logger.warning(f"Opening {out_html_Path=}")
        webbrowser.open(out_html_Path.resolve().as_uri())


    def set_v_info(self):
        # print("set_v_info called")
        set_version_info(webview.active_window())

    # ! def added_names_report(self):
    # !    added_names_report.main()


def get_entrypoint():

    if not APP_FROZEN:  # unfrozen development
        try:
            # must use the right port here, vite default is 5174.
            # Changed in vite.config.ts file
            url = 'http://localhost:5175'
            get = requests.get(url)
            if get.status_code == 200:
                return url
        except requests.exceptions.RequestException:
            print('Vite server not running. Trying static files')
        return Path('ui_bundle/index.html').resolve().as_uri()   # TODO: fix this

    py_2_app_path = Path("../Resources/ui_bundle/index.html")
    if py_2_app_path.exists():  # frozen py2app
        uri = py_2_app_path.resolve().as_uri()
        logger.info(f"{uri=}")
        return uri

    if hasattr(sys, '_MEIPASS'):
        # path to pyinstaller frozen app
        frozen_windows_ui_path = Path(sys._MEIPASS, 'ui/index.html')  # type: ignore
        logger.info(frozen_windows_ui_path)
        logger.info(frozen_windows_ui_path.exists())
        if frozen_windows_ui_path.exists():  # frozen pyinstaller
            uri = frozen_windows_ui_path.as_uri()
            logger.info(f"{uri=}")
            return uri

    time.sleep(5)

    raise Exception('No index.html found')



def main():
    with open("what.txt", "w") as f:
        for k, v in sys.__dict__.items():
            f.write(f"{k}: {v}\n")
    # print(repr(sys.__dict__))
    entry = get_entrypoint()

    logger.info(f"{entry=}")

    # html_ui_path = "../../ui_bundle/index.html"  # path if not frozen
    # if APP_FROZEN:
    #     # The application is frozen
    #     logger.info("App is frozen")
    #     # TODO: fix this path
    #     html_ui_path = "ui/pup_app_ui.html"

    try:
        logger.info(sys._MEIPASS)  # type: ignore
    except AttributeError:
        pass

    api = Api()

    global window
    window = webview.create_window(
        # url="file:///Users/mark/projects/pup-app/ui/pup_app_ui.html",  # no server
        # TODO: more robust solution to find the path to the html file
        url=entry,
        js_api=api,
        title="Lawchecker",
        width=1050,
        height=850,
        min_size=(450, 350),
        text_select=True,
        zoomable=True,
        # server=False,

    )

    print("Loaded")

    window = cast(Window, window)


    # window.events.loaded += on_loaded

    debug = not APP_FROZEN  # dont want to be in build app
    # debug = True

    # add ui logger
    gh_stream = io.StringIO("")
    gh = UILogHandler(gh_stream, window)
    gh.setLevel(level=logging.WARNING)
    logger.addHandler(gh)

    webview.start(
        debug=debug,
        storage_path=str(Path.home() / "pywebview" / "lawchecker"),
        # http_server=False,
    )


if __name__ == "__main__":
    main()
