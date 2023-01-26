#!/usr/bin/env python3

import os
import re
from pathlib import Path
import sys
from tempfile import mkdtemp
from typing import Optional
import webbrowser

# sys.path.append(str(Path(__file__).parent / 'pythonsaxon'))  # add saxonstuff to pythonpath
# print(sys.path)

# 3rd party saxon imports
# import nodekind  # type: ignore
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
    # from PyQt5 import QtCore

    from ui.addedNames import Ui_MainWindow


# we also need to set an environment variable
# I think this is for accessing:
    # libsaxon[EDITION].dylib - Saxon/C library
    # rt directory - Excelsior JET runtime which handles VM calls
    # saxon-data directory
os.environ["SAXONC_HOME"] = str(Path(Path(__file__).parent / 'saxonstuff').resolve())
print(os.environ.get("SAXONC_HOME", None))

XSLT_MARSHAL_PARAM_NAME = 'marsh-path'

DASH_XML_URL = "***REMOVED***" \
               "***REMOVED***"

XSL_1_NAME = 'added-names-spo-rest.xsl'
XSL_2_NAME = 'post-processing-html.xsl'

# path to folder containing the XSLT files
if hasattr(sys, 'executable') and hasattr(sys, '_MEIPASS'):
    # we are using the bundled app
    XSL_FOLDER = Path(sys.executable).parent / 'XSLT'
else:
    # assume running as python script via usual interpreter
    XSL_FOLDER = Path(__file__).parent / 'XSLT'
    if not XSL_FOLDER.exists():
        XSL_FOLDER = Path(__file__).parent.parent / 'XSLT'


XSL_1_PATH = XSL_FOLDER / XSL_1_NAME
XSL_2_PATH = XSL_FOLDER / XSL_2_NAME


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

    parser.add_argument('--marshal-dir', metavar='FM XML Folder', type=_dir_path,
                        help='Optional Path to the folder containing the XML files '
                             '(from FrameMaker) that you wish to use to marshal '
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

            self.fm_xml_folder = ''  # will be the fm xml folder path

            self.openBrowser_btn.clicked.connect(self.open_browser)

            self.xmlFile_btn.clicked.connect(self.open_dash_xml_file)

            self.fm_xml_btn.clicked.connect(self.open_fm_xml_folder)

            self.run_btn.clicked.connect(self.run)


        def open_browser(self):
            webbrowser.open(DASH_XML_URL)

        def open_dash_xml_file(self):
            self.dash_xml_file, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Open file', str(XSL_FOLDER.parent))

        def open_fm_xml_folder(self):
            self.fm_xml_folder = QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Select Folder')

        def run(self):

            fm_xml_folder_Path: Optional[Path] = None

            if self.fm_xml_folder:
                fm_xml_folder_Path = Path(self.fm_xml_folder)

            if self.dash_xml_file and Path(self.dash_xml_file).resolve().exists():
                xsl_1_Path = XSL_1_PATH
                xsl_2_Path = XSL_2_PATH
                input_Path = Path(self.dash_xml_file).resolve()
                try:
                    run_xslts(input_Path,
                              xsl_1_Path,
                              xsl_2_Path,
                              parameter=fm_xml_folder_Path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(window, 'Error', str(e))
            else:
                print('No XML file selected.')

    # use gui version
    app = QtWidgets.QApplication(args)

    # window = QtWidgets.QMainWindow()
    window = MainWindow()
    window.show()

    app.exec_()


def temp_fm_xml_files(parameter: Path) -> str:
    """Process FM XML files to remove docstring and save resultant files in a
    temp file. Return the parameter str in the form 'file:///C:/.../...'"""

    # lets also turn it into an absolute path
    parameter_abs = parameter.absolute()

    # now let's go through all the XML files in the folder and remove the doctypes
    fm_xml_files = list(parameter_abs.glob('*.xml'))

    # create a temporary directory
    temp_dir = mkdtemp(prefix='XML_from_FM')

    # loop through XML files
    for file in fm_xml_files:
        with open(file, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()

        root_start = 0  # line the root element starts at
        # remove anything before the root element
        for i, line in enumerate(file_lines):
            line_content = line.strip()
            if re.match(r'<[A-Za-z0-9._]', line_content):
                # found root
                root_start = i
                break

        # create new tempfile
        # tempfile, tempfilepath = mkstemp(suffix='.xml', prefix='FM')
        # output html to tempfile
        temp_tile_Path = Path(temp_dir, file.name)
        with open(temp_tile_Path, 'w', encoding='UTF-8') as fi:
            fi.writelines(file_lines[root_start:])
        print(f'Created: {temp_tile_Path}')


    # assume a windows path so switch \ for / and add
    # file:/// to beginning as this is how XSLT likes it
    parameter_str = temp_dir.replace("\\", "/")
    parameter_str = f'file:///{parameter_str}'
    print(f'parameter_str: {parameter_str}')

    return(parameter_str)



def run_xslts(input_Path: Path,
              xsl_1_Path: Path,
              xsl_2_Path: Path,
              parameter: Optional[Path] = None):

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


    intermidiate_Path = input_Path.with_name('intermidiate-from-python.xml').resolve()
    out_html_Path     = input_Path.with_name('output-from-python.html').resolve()

    with saxonche.PySaxonProcessor(license=False) as proc:

        # proc.set_configuration_property('ALLOWED_PROTOCOLS', 'all')

        print(proc.version)
        # print(f'{input_Path=}\n{xsl_1_Path=}\n{xsl_2_Path=}\n{intermidiate_Path=}\n{out_html_Path=}')

        input_path = str(input_Path)
        intermidiate_path = str(intermidiate_Path)
        outfilepath = str(out_html_Path)

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
            # get path to temp folder containing copied FM XML (with doctype removed)
            # and pass this to XSLT processor as a parameter.
            # This is for for marshelling.
            parameter_str = temp_fm_xml_files(parameter)

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
