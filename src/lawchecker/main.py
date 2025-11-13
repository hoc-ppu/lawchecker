import io
import json
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
from typing import Any, Literal, cast

import requests

try:
    import webview
    from webview import Window  # TODO: fix this
except ImportError as e:
    print('Error: pywebview is not installed. Please install it to run the GUI.')
    print('You may need to run: `pip install .[gui]` from the project root directory.')
    raise e

import lawchecker.lawchecker_logger as lawchecker_logger
from lawchecker import (
    __version__,
    added_names_report,
    check_web_amdts,
    common,
    pp_xml_lxml,
    settings,
)
from lawchecker.compare_amendment_documents import Report
from lawchecker.compare_bill_documents import Report as BillReport
from lawchecker.compare_bill_documents import diff_in_vscode
from lawchecker.compare_bill_numbering import CompareBillNumbering
from lawchecker.lawchecker_logger import logger
from lawchecker.ui_feedback import ProgressModal, UILogHandler

APP_FROZEN = getattr(sys, 'frozen', False)

logger.info('Main imports complete')

# Reference to the active window will be stored here
window: Window | None = None


# def set_version_info(window_local: Window | None = None):
#     # logger.info(f"{window_local=}")
#     if not window_local:
#         window_local = window
#     if not window_local:
#         logger.error('No window object.')
#         return

#     # match settings.RUNTIME_ENV:
#     #     case settings.RtEnv.EXE:
#     #         version_path = Path(sys._MEIPASS, "VERSION")  # type: ignore
#     #     case settings.RtEnv.APP:
#     #         version_path = Path("../Resources/VERSION")
#     #     case _:
#     #         version_path = Path("VERSION")

#     version_str = __version__

#     logger.info(f'{version_str=}')

#     # window_local.evaluate_js(f"updateVersionInfo('{version_str}')")
#     window_local.evaluate_js(f'window.pywebview.state.setVersionInfo("{version_str}")')


class Api:
    def __init__(self):
        self.com_bill_old_xml: Path | None = None
        self.com_bill_new_xml: Path | None = None

        self.com_compare_number_dir: Path | None = None

        self.dated_folder_Path: Path | None = None
        self.dash_xml_file: Path | None = None
        self.lm_xml_folder: Path | None = None
        self.existing_json_amdts_file: Path | None = None

        self.com_amend_old_xml: Path | None = None
        self.com_amend_new_xml: Path | None = None

        self.api_amend_xml: Path | None = None
        self.api_amend_json: Any = None

    def get_version(self) -> str:
        return __version__

    def print_from_js(self, string: str) -> None:
        print(string)

    def _open_file_dialog(self, file_type='') -> Path | None:
        # select a file

        active_window = cast(Window, common.RunTimeEnv.webview_window)

        if file_type == 'xml':
            file_types = ('XML files (*.xml)',)
        elif file_type == 'html':
            file_types = ('HTML files (*.html)',)
        else:
            file_types = ('All files (*.*)',)

        try:
            # result is None if the user cancels the dialog
            result = active_window.create_file_dialog(
                webview.FileDialog.OPEN, allow_multiple=False, file_types=file_types
            )
        except AttributeError:
            # occasionally on macos, if the user switches applications
            # the active window can be none
            result = None

        if result is None:
            return None

        return Path(result[0])

    def open_file_dialog(self, file_specifier: str, file_type='') -> str:
        # select a file

        _file = self._open_file_dialog(file_type)

        match file_specifier:
            case 'com_bill_old_xml':
                self.com_bill_old_xml = _file
            case 'com_bill_new_xml':
                self.com_bill_new_xml = _file
            case 'com_amend_old_xml':
                self.com_amend_old_xml = _file
            case 'com_amend_new_xml':
                self.com_amend_new_xml = _file
            case 'com_amend_api_xml':
                self.api_amend_xml = _file
            case 'existing_json_amdts':
                self.existing_json_amdts_file = _file
            case _:
                print(f'Error: Unknown file specifier: {file_specifier}')

        return str(_file)

    def select_folder(self, folder_specifier: str) -> None:
        print(f'select_folder called with folder_specifier: {folder_specifier}')

        active_window = cast(Window, common.RunTimeEnv.webview_window)

        result = active_window.create_file_dialog(
            webview.FileDialog.FOLDER, directory=str(Path.home())
        )

        if result is None:
            print('No folder selected.')
            return

        selected_folder = Path(result[0])
        print(f'Selected folder: {selected_folder}')

        match folder_specifier:
            case 'compare_number_dir':
                self.com_compare_number_dir = selected_folder
                print(f'compare_number_dir set to: {self.com_compare_number_dir}')
            case _:
                print(f'Error: Unknown folder specifier: {folder_specifier}')

    def anr_create_working_folder(self, date_str: str) -> str:
        """
        Create a working folder for the Added Names Report.

        @Called from: AddedNamesCollapsible <Button text="Create working folder">

        """

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')

            self.dated_folder_Path = settings.REPORTS_FOLDER.joinpath(formatted_date)
            self.dated_folder_Path.mkdir(parents=True, exist_ok=True)

            settings.GLOBAL_VARS.anr_working_folder = self.dated_folder_Path
            logger.info(f'{settings.GLOBAL_VARS.anr_working_folder=}')

            # create subfolders for dashboard XML (and intermediate)
            # as well as lawmaker/framemaker XML
            anr_lawmaker_xml = self.dated_folder_Path.joinpath(settings.XML_FOLDER)
            anr_lawmaker_xml.mkdir(parents=True, exist_ok=True)
            dashboard_data = self.dated_folder_Path.joinpath(
                settings.DASHBOARD_DATA_FOLDER
            )
            dashboard_data.mkdir(parents=True, exist_ok=True)

            return f'Working folder created: {self.dated_folder_Path}'
        except Exception as e:
            return f'Error: Could not create folder {repr(e)}'

    def open_folder(self, folder_path: str) -> str:
        """
        Open a folder in the default file manager.
        """

        try:
            if platform.system() == 'Windows':
                os.startfile(folder_path)  # type: ignore
            elif platform.system() == 'Darwin':
                # macOS
                subprocess.run(['open', folder_path])
            else:
                # Linux and other Unix-like systems
                subprocess.run(['xdg-open', folder_path])

            msg = f'Opened folder: {folder_path}'
            logger.info(msg)
            return msg

        except Exception as e:
            msg = f'Could not open folder {repr(e)}'
            logger.error(msg)
            return f'Error: {msg}'

    def open_dash_xml_in_browser(self) -> str:
        """
        Loads the Added Names dashboard XML in the default web browser.

        The user must download this first as there is security
        so we can't request it directly.
        """
        if not settings.DASH_XML_URL:
            logger.warning(
                'No DASH_XML_URL set in settings. Likely there is no .env file'
                '\nPlease create a .env file in the root of the project'
                ' see .env.example for an example of the required format.'
            )
        try:
            webbrowser.open(settings.DASH_XML_URL)  # type: ignore
            logger.info('Dashboard XML opened in browser.')
        except Exception as e:
            logger.error(f'Error: Could not open browser {repr(e)}')

    def open_dash_xml_file(self) -> str:
        """
        Opens a file dialog to select the dashboard XML file.
        """
        default_location = (
            settings.PARENT_FOLDER
        )  # if user did not create working folder
        if self.dated_folder_Path is not None:
            default_location = self.dated_folder_Path / settings.DASHBOARD_DATA_FOLDER

        active_window = cast(Window, common.RunTimeEnv.webview_window)

        result = active_window.create_file_dialog(
            webview.FileDialog.OPEN,
            directory=str(default_location),
            # Allow all files instead of just XML. This is because when users
            # download the data from sharepoint it is saved as .txt. It is
            # easier for uses to be able to select the .txt file rather than
            # first having to change the file extension.
            # , file_types=("XML files (*.xml)",)
        )

        if result is None:
            return 'No file selected.'

        self.dash_xml_file = Path(result[0])
        return f'Selected file: {self.dash_xml_file}'

    def anr_open_amd_xml_dir(self) -> str:
        """
        Open a directory selection dialog to select the amendment XML directory.
        """
        default_location = settings.PARENT_FOLDER
        if self.dated_folder_Path is not None:
            default_location = self.dated_folder_Path

        active_window = cast(Window, common.RunTimeEnv.webview_window)

        result = active_window.create_file_dialog(
            webview.FileDialog.FOLDER, directory=str(default_location)
        )

        if result is None:
            return 'No directory selected.'

        self.lm_xml_folder = Path(result[0])
        return f'Selected directory: {self.lm_xml_folder}'

    def anr_run_xslts(self) -> str:
        """
        Run the transforms  to create the Added Names report.
        """
        lm_xml_folder_Path: Path | None = None

        if self.lm_xml_folder:
            lm_xml_folder_Path = Path(self.lm_xml_folder)

        if not (self.dash_xml_file and Path(self.dash_xml_file).resolve().exists()):
            return 'No XML file selected.'

        input_Path = Path(self.dash_xml_file).resolve()

        try:
            with ProgressModal() as modal:
                modal.update(f'Dashboard XML: {self.dash_xml_file}')

                if self.lm_xml_folder:
                    modal.update(f'Marshal XML: {self.lm_xml_folder}')
                else:
                    modal.update('No marshal XML selected')

                modal.update('Running...')
                added_names_report.run_xslts(input_Path, parameter=lm_xml_folder_Path)
                modal.update('Report ready.')

            return 'Report created successfully.'

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return f'Error: {str(e)}'

    def _create_html_compare(
        self,
        report_type: Literal['bills', 'amendments'],
        days_between_papers: bool = False,
    ):
        """
        Create the compare report for either bills or amendments
        """

        if report_type == 'bills':
            old_xml_path = self.com_bill_old_xml
            new_xml_path = self.com_bill_new_xml
        elif report_type == 'amendments':
            old_xml_path = self.com_amend_old_xml
            new_xml_path = self.com_amend_new_xml
        else:
            raise ValueError(f'Unknown report type: {report_type}')

        # TODO: add better validation and error handling
        if not old_xml_path:
            logger.error('No old XML file selected.')
            return

        if not new_xml_path:
            logger.error('No new XML file selected.')
            return

        # Check the Old and New XML files can both be parsed as XML
        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        # TODO: Improve the below
        if not old_xml:
            logger.error(f'Old XML file is not valid XML: {old_xml_path}')
            return

        if not new_xml:
            logger.error(f'New XML file is not valid XML: {new_xml_path}')
            return

        if report_type == 'bills':
            report = BillReport(
                old_xml_path,
                new_xml_path,
            )
            # TODO: should probably add the normalised truncated bill title
            report_file_name = 'Comp_Bills.html'

        elif report_type == 'amendments':
            report = Report(
                old_xml_path,
                new_xml_path,
                days_between_papers,
            )
            report_file_name = f'Comp_Amdts_{report.old_doc.short_file_name}.html'

        with ProgressModal() as modal:
            modal.update(f'Old XML path: {old_xml_path}', log=True)
            modal.update(f'New XML path: {new_xml_path}', log=True)

            out_html_path = old_xml_path.parent.joinpath(report_file_name)

            report.html_tree.write(
                str(out_html_path),
                method='html',
                encoding='utf-8',
                doctype='<!DOCTYPE html>',
            )

            modal.update(f'HTML report created: {out_html_path}', log=True)
            modal.update('Attempting to open in browser...')

            webbrowser.open(out_html_path.resolve().as_uri())

    def bill_create_html_compare(self):
        """Create the compare report for bills"""

        self._create_html_compare('bills')

    def bill_compare_in_vs_code(self):
        if not self.com_bill_old_xml:
            logger.error('No old XML file selected.')
            return

        if not self.com_bill_new_xml:
            logger.error('No new XML file selected.')
            return

        old_xml_path = Path(self.com_bill_old_xml).resolve()
        new_xml_path = Path(self.com_bill_new_xml).resolve()

        # Check the Old and New XML files can both be parsed as XML

        old_xml = pp_xml_lxml.load_xml(str(old_xml_path))
        new_xml = pp_xml_lxml.load_xml(str(new_xml_path))

        if not old_xml:
            logger.error(f'Old XML file is not valid XML: {old_xml_path}')
            return

        if not new_xml:
            logger.error(f'New XML file is not valid XML: {new_xml_path}')
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
        print('compare_bill_numbering called')

        if not self.com_compare_number_dir:
            print('Error: No directory selected.')
            return 'Error: No directory selected.'

        compare_dir = Path(self.com_compare_number_dir).resolve()
        print(f'compare_dir resolved to: {compare_dir}')

        if not compare_dir.is_dir():
            print('Error: Selected path is not a directory.')
            return 'Error: Selected path is not a directory.'

        compare = CompareBillNumbering.from_folder(compare_dir)
        print('CompareBillNumbering instance created')

        created_files = compare.save_csv(compare_dir)
        print('CSV files created')
        if created_files:
            with ProgressModal() as modal:
                for file in created_files:
                    modal.update(f'CSV file created: {file}')

    def amend_create_html_compare(self, days_between_papers=False):
        """
        Create the compare report for amendments
        """

        self._create_html_compare('amendments', days_between_papers)

    def get_api_amendments_using_xml_for_params(
        self,
        file: Path | str | None,
        save_json: bool = True,
    ) -> None:
        """
        Query the Bills API for the amendments by first extracting data from the XML file.
        """
        if not file:
            # do we need an error here?
            logger.notice('No XML file selected.')
            return

        if not isinstance(file, Path):
            file = Path(file)

        if not file.exists():
            logger.error(f'File does not exist: {file}')
            return

        logger.info(f'file path: {file}')

        json_amdts = None

        with ProgressModal() as modal:
            modal.update('Querying Bills API for amendments. Please wait...')
            try:
                json_amdts = check_web_amdts.also_query_bills_api(file, save_json)
                if not json_amdts:
                    logger.error('No JSON returned from API.')
            except Exception as e:
                logger.error(f'Error querying API: {repr(e)}')

            modal.update('Query complete.')

        self.api_amend_json = json_amdts

    def get_api_amendments_with_ids(
        self, bill_id: str, stage_id: str, save_json: bool = True
    ) -> None:
        """
        Query the Bills API for the amendments using the bill and stage IDs.
        """
        logger.info(
            f'get_api_amendments_with_ids called with {bill_id=} and {stage_id=}'
        )
        if not bill_id or not stage_id:
            logger.error('Bill ID and Stage ID are required.')
            return
        try:
            bill_id_int = int(bill_id)
            stage_id_int = int(stage_id)
        except ValueError:
            logger.error('Bill ID and Stage ID must be integers.')
            return

        if save_json:
            # we must have an xml file as the JSON file will be saved next to it
            if not self.api_amend_xml:
                logger.error('No XML file selected.')
                return

        with ProgressModal() as modal:
            modal.update('Querying Bills API for amendments. Please wait...')
            try:
                amendments_summary_json = check_web_amdts.get_amendments_summary_json(
                    bill_id, stage_id
                )
                print(len(amendments_summary_json))
                json_amdts = check_web_amdts.get_amendments_detailed_json(
                    amendments_summary_json, bill_id_int, stage_id_int
                )
                if not json_amdts:
                    logger.error('No JSON returned from API.')
            except Exception as e:
                logger.error(f'Error querying API: {e}')
            else:
                if save_json:
                    file_path = (
                        Path(self.api_amend_xml).parent
                        / f'{bill_id}_{stage_id}_amdts.json'
                    )
                    check_web_amdts.save_json_to_file(json_amdts, file_path)

                self.api_amend_json = json_amdts

            modal.update('Query complete.')

    def data_is_avaliable(self) -> bool:
        """
        Check if the API data is available.
        """
        if not self.api_amend_xml:
            logger.error('No XML file selected.')
            return False
        if not self.api_amend_json:
            if self.existing_json_amdts_file:
                try:
                    with open(self.existing_json_amdts_file, 'r') as f:
                        self.api_amend_json = json.load(f)
                except Exception as e:
                    logger.error(f'Error loading JSON file: {repr(e)}')
                    return False
            else:
                logger.error('No JSON data available.')
                return False

        return True

    # def create_api_csv(self):
    #     if not self.data_is_avaliable():
    #         return
    #     report = check_web_amdts.Report(self.api_amend_xml, self.api_amend_json)

    #     # logger.info([key for key in report.json_amdts.keys()])
    #     logger.notice(f'stage_id: {report.json_amdts.stage_id}')
    #     logger.notice(f'bill_id: {report.json_amdts.bill_id}')

    #     report.create_csv()
    #     # logger.warning("main.create_api_csv called")

    def create_api_report(self):
        if not self.data_is_avaliable():
            return
        report = check_web_amdts.Report(self.api_amend_xml, self.api_amend_json)

        # filename = "API_html_diff.html"

        bill_title = report.json_amdts.meta_bill_title
        bill_stage = report.json_amdts.stage_name
        xml_file_path = report.xml_file_path
        if xml_file_path:
            parent_path = xml_file_path.resolve().parent
        else:
            parent_path = Path.cwd()

        if bill_stage is not None:
            file_name = f'{bill_title}_{bill_stage}_amdt_table.html'
        else:
            file_name = f'{bill_title}_amdt_report.html'

        file_path = parent_path / file_name

        logger.info(f'Attempting to write report to {file_path}')

        report.html_tree.write(
            str(file_path),
            method='html',
            encoding='utf-8',
            doctype='<!DOCTYPE html>',
        )

        logger.info('Report written')

        webbrowser.open(Path(file_path).resolve().as_uri())


def get_entrypoint():
    if not APP_FROZEN:  # unfrozen development
        logger.info('App is not frozen')

        # must use the right port here, we use 5174.
        # Changed in vite.config.ts file
        url = 'http://localhost:5175'

        # Developers do often use the dev server to try things out but not
        # always as they may want to test the bundled HTML.
        # so we will check if it is running first

        for _ in range(20):
            try:
                get = requests.get(url, timeout=0.05)
                if get.status_code == 200:
                    return url
            except Exception:
                pass
            time.sleep(0.05)

        logger.info('Vite server not running. Trying static files')
        return Path('ui_bundle/index.html').resolve().as_uri()  # TODO: fix this

    py_2_app_path = Path('../Resources/ui_bundle/index.html')
    if py_2_app_path.exists():  # frozen py2app
        uri = py_2_app_path.resolve().as_uri()
        logger.info(f'{uri=}')
        return uri

    if hasattr(sys, '_MEIPASS'):
        # path to pyinstaller frozen app
        frozen_windows_ui_path = Path(sys._MEIPASS, 'ui/index.html')  # type: ignore
        logger.info(frozen_windows_ui_path)
        logger.info(frozen_windows_ui_path.exists())
        if frozen_windows_ui_path.exists():  # frozen pyinstaller
            uri = frozen_windows_ui_path.as_uri()
            logger.info(f'{uri=}')
            return uri

    time.sleep(5)

    raise FileNotFoundError('No index.html found')


def main():
    logger.info('Starting Lawchecker main function')
    # with open("what.txt", "w") as f:
    #     for k, v in sys.__dict__.items():
    #         f.write(f"{k}: {v}\n")

    entry = get_entrypoint()

    logger.info(f'{entry=}')

    # html_ui_path = "../../ui_bundle/index.html"  # path if not frozen
    # if APP_FROZEN:
    #     # The application is frozen
    #     logger.info("App is frozen")
    #     # TODO: fix this path
    #     html_ui_path = "ui/pup_app_ui.html"

    try:
        logger.info(sys._MEIPASS)  # type: ignore
        logger.info(Path(__file__).resolve())
    except AttributeError:
        pass

    api = Api()

    try:
        window = webview.create_window(
            url=entry,
            js_api=api,
            title='Lawchecker',
            width=1050,
            height=850,
            min_size=(450, 350),
            text_select=True,
            zoomable=True,
            # server=False,
        )
    except Exception as e:
        logger.error(f'Error creating webview window: {repr(e)}')
        raise e

    common.RunTimeEnv.webview_window = cast(Window, window)

    print('Nearly there...')
    logger.info('Main window created')

    debug = not APP_FROZEN  # no debug in build app
    # debug = True

    # add ui logger
    gh_stream = io.StringIO('')
    gh = UILogHandler(gh_stream, window)
    gh.setLevel(level=lawchecker_logger.NOTICE_LEVEL)
    logger.addHandler(gh)

    try:
        webview.start(
            debug=debug,
            storage_path=str(Path.home() / 'pywebview' / 'lawchecker'),
            # http_server=False,
        )
    except Exception as e:
        logger.error(f'Error starting webview: {repr(e)}')
        raise e


if __name__ == '__main__':
    main()
