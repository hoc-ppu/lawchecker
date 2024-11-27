import platform
import sys
import tomllib
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Callable, cast

import requests
import webview
from webview import Window

from lawchecker.lawchecker_logger import logger  # must be before submodules...
from lawchecker import added_names_report, settings
from lawchecker.compare_amendment_documents import Report
from lawchecker.compare_bill_documents import Report as BillReport
from lawchecker.compare_bill_documents import diff_in_vscode
from lawchecker.compare_bill_numbering import CompareBillNumbering
from lawchecker.settings import ANR_WORKING_FOLDER, NSMAP
from lawchecker.submodules.python_toolbox import pp_xml_lxml
from lawchecker.ui.addedNames import Ui_MainWindow

APP_FROZEN = getattr(sys, 'frozen', False)

print("Hello")

def set_version_info(window):

    pyproject_path = Path("pyproject.toml")
    if APP_FROZEN:
        pyproject_path = Path(sys._MEIPASS, "pyproject.toml")

    with open(pyproject_path, 'rb') as f:
        toml_data = tomllib.load(f)

    version_str = toml_data.get('project', {}).get("version", "No version info")
    logger.info(f"{version_str=}")

    # window.evaluate_js(f"updateVersionInfo('{version_str}')")
    window.evaluate_js(f"window.pywebview.state.setVersionInfo(\"{version_str}\")")

class Api:
    def __init__(self):
        self.com_bill_old_xml: Path | None = None
        self.com_bill_new_xml: Path | None = None

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


    def open_file_dialog(self, file_specifier: str, file_type="") -> None:
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


    def bill_create_html_compare(self):
        """
        Create the compare report for bills
        """
        print("here")

        # TODO: add better validation and error handling
        if not self.com_bill_old_xml:
            print("Error", "No old XML file selected.")
            return

        if not self.com_bill_new_xml:
            print("Error", "No new XML file selected.")
            return

        old_xml_path = Path(self.com_bill_old_xml).resolve()
        new_xml_path = Path(self.com_bill_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        print()

        # TODO: Improve the below
        if not old_xml:
            print("Error", f"Old XML file is not valid XML: {old_xml_path}")
            return

        if not new_xml:
            print("Error", f"New XML file is not valid XML: {new_xml_path}")
            return


        out_html_Path = old_xml_path.parent.joinpath("Compare_Bills.html")

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

        webbrowser.open(out_html_Path.resolve().as_uri())

    def bill_compare_in_vs_code(self):

        if not self.com_bill_old_xml:
            print("Error", "No old XML file selected.")
            return

        if not self.com_bill_new_xml:
            print("Error", "No new XML file selected.")
            return

        old_xml_path = Path(self.com_bill_old_xml).resolve()
        new_xml_path = Path(self.com_bill_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        if not old_xml:
            print("Error", f"Old XML file is not valid XML: {old_xml_path}")
            return

        if not new_xml:
            print("Error", f"New XML file is not valid XML: {new_xml_path}")
            return

        report = BillReport(
            old_xml_path,
            new_xml_path,
        )

        diff_in_vscode(report.old_doc.root, report.new_doc.root)


    def amend_create_html_compare(
        self, days_between_papers=False
    ):
        """
        Create the compare report for amendments
        """

        bla = f"amend_create_html_compare called\n {days_between_papers=}"
        print(
            bla
        )

        logger.warning(bla)

        # TODO: add better validation and error handling
        if not self.com_amend_old_xml:
            msg = "Error", "No old XML file selected."
            logger.error(msg)
            return

        if not self.com_amend_new_xml:
            msg = "Error", "No new XML file selected."
            logger.error(msg)
            return

        old_xml_path = Path(self.com_amend_old_xml).resolve()
        new_xml_path = Path(self.com_amend_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        print()

        # TODO: Improve the below
        if not old_xml:
            msg = "Error", f"Old XML file is not valid XML: {old_xml_path}"
            logger.error(msg)
            return

        if not new_xml:
            msg = "Error", f"New XML file is not valid XML: {new_xml_path}"
            logger.error(msg)
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
        return '../gui/index.html'   # TODO: fix this

    # if exists('../Resources/gui/index.html'):  # frozen py2app
    #     return '../Resources/gui/index.html'

    # if exists('../gui/gui/index.html'):
    #     return '../gui/gui/index.html'

    raise Exception('No index.html found')



def main():
    entry = get_entrypoint()

    # html_ui_path = "../../dist/index.html"  # path if not frozen
    # if APP_FROZEN:
    #     # The application is frozen
    #     logger.info("App is frozen")
    #     # TODO: fix this path
    #     html_ui_path = "ui/pup_app_ui.html"

    try:
        logger.info(sys._MEIPASS)
    except AttributeError:
        pass

    api = Api()
    print("Hello")
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
        # transparent=True,
        # vibrancy=True,
        # frameless=False
    )

    # window.events.loaded += on_loaded

    debug = sys.platform != "win32"  # dont want to be in debug mode on windows
    # debug = True

    webview.start(
        debug=debug,
        storage_path=str(Path.home() / "pywebview"),
        # http_server=False,
    )


if __name__ == "__main__":
    main()
