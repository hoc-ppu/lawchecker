#!/usr/bin/env python3

from datetime import datetime
import os
import re
from pathlib import Path
import sys
import traceback
from typing import Optional
import webbrowser


# 3rd party saxon imports
import saxonche


USE_GUI = True

# --- conditional imports ---
if len(sys.argv) > 1:
    USE_GUI = False
    # comand line only imports
    import argparse
else:
    # GUI only imports
    from PyQt5 import QtWidgets
    from PyQt5 import QtCore

    from ui.addedNames import Ui_MainWindow


XSLT_MARSHAL_PARAM_NAME = 'marsh-path'

DASH_XML_URL = "***REMOVED***" \
               "***REMOVED***"

XSL_1_NAME = 'added-names-spo-rest.xsl'
XSL_2_NAME = 'post-processing-html.xsl'

LAWMAKER_XML_FOLDER_NAME = 'Lawmaker_XML_Files'
DASHBOARD_DATA_FOLDER_NAME = 'Dashboard_Data'

# path to folder containing the XSLT files
if hasattr(sys, 'executable') and hasattr(sys, '_MEIPASS'):
    # we are using the bundled app
    PARENT_FOLDER = Path(sys.executable).parent
else:
    # assume running as python script via usual interpreter
    PARENT_FOLDER = Path(__file__).parent
    if not PARENT_FOLDER.joinpath('XSLT').exists():
        PARENT_FOLDER = PARENT_FOLDER.parent

XSL_FOLDER = PARENT_FOLDER / 'XSLT'

REPORTS_FOLDER = PARENT_FOLDER / '_Reports'

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
        description='Create an HTML report of added names from XML downloaded form the Dashboard')

    parser.add_argument('file', metavar='XML File', type=open,
                        help='File path to the XML you wish to process. '
                             'Use quotes if there are spaces.')

    parser.add_argument('--xslts', metavar='XSLT Folder', type=_dir_path,
                        help='Path to the folder containing the XSLTs wish to run. '
                             'Use quotes if there are spaces.')

    parser.add_argument('--marshal-dir', metavar='LM XML Folder', type=_dir_path,
                        help='Optional Path to the folder containing the XML files '
                             '(from LawMaker) that you wish to use to marshal '
                             'the report. Use quotes if there are spaces.')


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
        marshal_dir = args.marshal_dir
    else:
        marshal_dir = None


    print(f'marshal_dir={marshal_dir}')
    run_xslts(input_Path, xsl_1_Path, xsl_2_Path, parameter=Path(marshal_dir))



def gui(args):

    class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
        def __init__(self, *args, obj=None, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.setupUi(self)

            self.dash_xml_file = ''  # will be the xml file path

            self.lm_xml_folder = ''  # will be the lm xml folder path

            self.workingFolderDateEdit.setDate(QtCore.QDate.currentDate())
            self.createWorkingFolderBtn.clicked.connect(self.create_working_folder)

            self.openBrowser_btn.clicked.connect(self.open_browser)

            self.xmlFile_btn.clicked.connect(self.open_dash_xml_file)

            self.fm_xml_btn.clicked.connect(self.open_lm_xml_folder)

            self.run_btn.clicked.connect(self.run)

            self.dated_folder_Path: Optional[Path] = None


        def create_working_folder(self):
            date_obj = self.workingFolderDateEdit.date().toPyDate()
            formatted_date = date_obj.strftime("%Y-%m-%d")

            try:
                self.dated_folder_Path = REPORTS_FOLDER.joinpath(formatted_date)
                self.dated_folder_Path.mkdir(parents=True, exist_ok=True)
                QtWidgets.QMessageBox.information(window, 'Info', f'Working folder is:  {self.dated_folder_Path}')

                global WORKING_FOLDER
                WORKING_FOLDER = self.dated_folder_Path

                # create subfolders for dashboard XML (and intermediate)
                # as well as lawmaker XML
                lawmaker_xml = self.dated_folder_Path.joinpath(LAWMAKER_XML_FOLDER_NAME)
                lawmaker_xml.mkdir(parents=True, exist_ok=True)
                dashboard_data = self.dated_folder_Path.joinpath(DASHBOARD_DATA_FOLDER_NAME)
                dashboard_data.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QtWidgets.QMessageBox.critical(window, 'Error', f'Could not create folder {repr(e)}')



        def open_browser(self):
            webbrowser.open(DASH_XML_URL)

        def open_dash_xml_file(self):
            if self.dated_folder_Path is not None:
                default_location = self.dated_folder_Path
            else:
                default_location = PARENT_FOLDER
            self.dash_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open file', str(default_location))

        def open_lm_xml_folder(self):
            self.lm_xml_folder = QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Select Folder', str(self.dated_folder_Path))

        def run(self):

            lm_xml_folder_Path: Optional[Path] = None

            if self.lm_xml_folder:
                lm_xml_folder_Path = Path(self.lm_xml_folder)

            if self.dash_xml_file and Path(self.dash_xml_file).resolve().exists():
                xsl_1_Path = XSL_1_PATH
                xsl_2_Path = XSL_2_PATH
                input_Path = Path(self.dash_xml_file).resolve()
                try:
                    run_xslts(input_Path,
                              xsl_1_Path,
                              xsl_2_Path,
                              parameter=lm_xml_folder_Path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(window, 'Error', str(e))
                    print(traceback.print_exc(file=sys.stdout))
            else:
                print('No XML file selected.')

    # use gui version
    app = QtWidgets.QApplication(args)

    # window = QtWidgets.QMainWindow()
    window = MainWindow()
    window.show()

    app.exec_()


def extract_date(input_Path: Path) -> str:
    """Extract date form input XML from SharePoint"""

    with open(input_Path) as f:
        input_xml_str = f.read()

    print(f'input_xml_str length is: {len(input_xml_str)}')
    # get the updated date
    match = re.search(r'(<updated>)([A-Z0-9:+-]+)(</updated>)', input_xml_str)
    date_str = ''
    if match:
        print('match found')
        date_str = match.group(2)
        print(f'{date_str=}')

    try:
        dt = datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
        formated_date = dt.strftime("%Y-%m-%d__%H-%M")
    except Exception as e:
        print(repr(e))
        formated_date = ''

    return formated_date



def run_xslts(input_Path: Path,
              xsl_1_Path: Path,
              xsl_2_Path: Path,
              parameter: Optional[Path] = None):

    print(f'{input_Path=}')
    print(f'{xsl_1_Path=}')
    print(f'{xsl_2_Path=}')
    print(f'{parameter=}')

    try:
        # check xsl paths are valid
        xsl_1_Path = xsl_1_Path.absolute().resolve(strict=True)
        xsl_2_Path = xsl_2_Path.absolute().resolve(strict=True)
    except FileNotFoundError as e:
        err_txt = ('The following required XSLT files are missing:'
                   f'\n\n{xsl_1_Path}\n\n{xsl_2_Path}'
                   '\n\nUsually you should have two XSL files in a folder called \'XSLT\''
                   ' and that folder should be in the same folder as this program.')
        print('Error:', err_txt)
        if USE_GUI:
            # this can be caught in the GUI code and the Error message displayed in a GUI window
            raise Exception(err_txt) from e
        return


    formated_date = extract_date(input_Path)

    intermediate_file_name = f"{formated_date}_intermediate.xml"
    input_file_resave_name = f"{formated_date}_input_from_SP.xml"
    output_file_name = f"Added_Names_Report.html"


    # intermidiate_Path = input_Path.with_name('intermidiate-from-python.xml').resolve()
    # out_html_Path     = input_Path.with_name('output-from-python.html').resolve()
    if WORKING_FOLDER is None:
        dated_folder_Path = REPORTS_FOLDER.joinpath(formated_date).resolve()
    else:
        dated_folder_Path = WORKING_FOLDER.resolve()
    dated_folder_Path.mkdir(parents=True, exist_ok=True)
    xml_folder_Path = dated_folder_Path.joinpath(DASHBOARD_DATA_FOLDER_NAME)
    xml_folder_Path.mkdir(parents=True, exist_ok=True)

    intermidiate_Path = xml_folder_Path.joinpath(intermediate_file_name)
    out_html_Path     = dated_folder_Path.joinpath(output_file_name)

    print(f'{intermidiate_Path=}')
    print(f'{out_html_Path=}')

    # resave the input file
    resave_Path = xml_folder_Path.joinpath(input_file_resave_name)
    with open(resave_Path, 'w') as f:
        f.write(input_Path.read_text())

    with saxonche.PySaxonProcessor(license=False) as proc:

        # proc.set_configuration_property('ALLOWED_PROTOCOLS', 'all')

        print(proc.version)
        # print(f'{input_Path=}\n{xsl_1_Path=}\n{xsl_2_Path=}\n{intermidiate_Path=}\n{out_html_Path=}')

        # need to be as uri in case there are spaces in the path
        input_path = input_Path.as_uri()
        intermidiate_path = intermidiate_Path.as_uri()
        outfilepath = out_html_Path.as_uri()

        # --- 1st XSLT ---
        xsltproc = proc.new_xslt30_processor()

        # document = proc.parse_xml(xml_file_name=str(input_Path))
        # xsltproc.set_source_node(xdm_node=document)

        executable = xsltproc.compile_stylesheet(stylesheet_file=str(xsl_1_Path))
        # xsltproc.set_jit_compilation(True)
        executable.transform_to_file(source_file=input_path, output_file=intermidiate_path)


        # --- 2nd XSLT ---
        xsltproc2 = proc.new_xslt30_processor()

        executable2 = xsltproc2.compile_stylesheet(stylesheet_file=str(xsl_2_Path))

        if parameter:
            # get path to folder containing LawMaker XML file(s)
            # and pass this to XSLT processor as a parameter.
            # This is for for marshelling.

            parameter_str = parameter.as_uri()  # uri works best with Saxon
            param = proc.make_string_value(parameter_str)

            executable2.set_parameter(XSLT_MARSHAL_PARAM_NAME, param)

        executable2.transform_to_file(source_file=str(intermidiate_Path), output_file=outfilepath)

        # --- finished transforms ---

        print(f'Created: {outfilepath}')

        if os.name == 'posix':
            webbrowser.open('file://' + outfilepath)
        else:
            webbrowser.open(outfilepath)

        print('Done.')


if __name__ == '__main__':
    main()
