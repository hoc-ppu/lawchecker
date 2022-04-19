#!/usr/bin/env python3

import os
from pathlib import Path
import sys
# from tempfile import mkstemp
from typing import Optional
import webbrowser


sys.path.append(str(Path(__file__).parent / 'pythonsaxon')) # add saxonstuff to pythonpath
# print(sys.path)

# 3rd party saxon imports
import nodekind  # type: ignore
import saxonc


# conditional imports
if len(sys.argv) > 1:
    USE_GUI = False
    # comand line only imports
    import argparse
else:
    USE_GUI = True
    # GUI only imports
    from PyQt5 import QtWidgets
    # from PyQt5 import QtCore
    getOpenFileName = QtWidgets.QFileDialog.getOpenFileName

    from ui.addedNames import Ui_MainWindow

# we also need to set an envoroment variable
# I think this is for accessing:
    # libsaxon[EDITION].dylib - Saxon/C library
    # rt directory - Excelsior JET runtime which handles VM calls
    # saxon-data directory
os.environ["SAXONC_HOME"] = str(Path(Path(__file__).parent / 'saxonstuff').resolve())
print(os.environ.get("SAXONC_HOME", None))

DASH_XML_URL = "https://hopuk.sharepoint.com/sites/bct-ppu/_api/web/lists/" \
               "GetByTitle('Added%20Names')/items?$filter=Checked_x003f_%20eq%20%27false%27"

XSL_1_NAME = 'added-names-spo-rest.xsl'
XSL_2_NAME = 'post-processing-html.xsl'

# path to folder contining the XSLT files
if hasattr(sys, 'executable') and hasattr(sys, '_MEIPASS'):
    # we are using the bundled app
    XSL_FOLDER = Path(sys.executable).parent / 'XSLT'
else:
    # assume running as python script via usual interpreter
    XSL_FOLDER = Path(__file__).parent / 'XSLT'


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
                        help='Path to the folder containg the XSLTs wish to run. '
                             'Use quotes if there are spaces.')

    parser.add_argument('--marshal-dir', metavar='FM XML Folder', type=_dir_path,
                        help='Optional Path to the folder containg the XML files '
                             '(from FrameMaker) that you wish to use to marshal '
                             'the report. Use quotes if there are spaces.')


    args = parser.parse_args(cli_args[1:])
    # print(args)

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

    run_xslts(input_Path, xsl_1_Path, xsl_2_Path, xslt_parameter=marshal_dir)



def gui(args):
 
    class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
        def __init__(self, *args, obj=None, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
            self.setupUi(self)

            self.dash_xml_file = ''  # will be the xml file path

            self.openBrowser_btn.clicked.connect(self.open_browser)

            self.xmlFile_btn.clicked.connect(self.open_dash_xml_file)

            self.run_btn.clicked.connect(self.run)

        
        def open_browser(self):
            webbrowser.open(DASH_XML_URL)
        def open_dash_xml_file(self):
            self.dash_xml_file, _ = getOpenFileName(self, 'Open file', str(Path.home()))

        def run(self):

            if self.dash_xml_file and Path(self.dash_xml_file).resolve().exists():
                xsl_1_Path = XSL_1_PATH
                xsl_2_Path = XSL_2_PATH
                input_Path = Path(self.dash_xml_file).resolve()
                try:
                    run_xslts(input_Path, xsl_1_Path, xsl_2_Path)
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

    

def run_xslts(input_Path: Path, xsl_1_Path: Path, xsl_2_Path: Path, xslt_parameter: Optional[str]):

    if xslt_parameter:
        # assume a windows path so switch \ for /
        # also add file:/// to begining
        xslt_parameter = f'file:///{xslt_parameter.replace("\\", "/")}'

    # check xsl paths are valid
    try:
        xsl_1_Path = xsl_1_Path.absolute().resolve(strict=True)
        xsl_2_Path = xsl_2_Path.absolute().resolve(strict=True)
    except FileNotFoundError as e:
        err_txt = f'The following required XSLT files are missing:\n\n{xsl_1_Path}\n\n{xsl_2_Path}' \
                  '\n\nUsually you should have two XSL files in a folder called \'XSLT\'' \
                  ' and that folder should be in the same folder as this program.'
        print('Error:', err_txt)
        if USE_GUI:
            # this can be caught in the GUI code and the Error message displayed in a GUI window
            raise Exception(err_txt) from e
        return
 

    intermidiate_Path = input_Path.with_name('intermidiate-from-python.xml').resolve()
    out_html_Path     = input_Path.with_name('output-from-python.html').resolve()

    # _, tempfilepath = mkstemp(suffix='.html', prefix='Dashboard')

    with saxonc.PySaxonProcessor(license=False) as proc:

        print(proc.version)
        # print(f'{input_Path=}\n{xsl_1_Path=}\n{xsl_2_Path=}\n{intermidiate_Path=}\n{out_html_Path=}')

        # 1st XSLT
        xsltproc = proc.new_xslt_processor()

        document = proc.parse_xml(xml_file_name=str(input_Path))

        xsltproc.set_source(xdm_node=document)

        xsltproc.compile_stylesheet(stylesheet_file=str(xsl_1_Path))

        xsltproc.set_jit_compilation(True)

        xsltproc.set_output_file(str(intermidiate_Path))

        xsltproc.transform_to_file()

        # 2nd XSLT
        xsltproc2 = proc.new_xslt_processor()

        document2 = proc.parse_xml(xml_file_name=str(intermidiate_Path))
        xsltproc2.set_source(xdm_node=document2)

        xsltproc2.compile_stylesheet(stylesheet_file=str(xsl_2_Path))

        xsltproc2.set_jit_compilation(True)

        tempfilepath = str(out_html_Path)

        if xslt_parameter:
            xsltproc2.set_parameter('marsh-path', xslt_parameter)

        xsltproc2.set_output_file(tempfilepath)

        xsltproc2.transform_to_file()

        print(f'Created: {tempfilepath}')

        if os.name == 'posix':
            webbrowser.open('file://' + tempfilepath)
        else:
            webbrowser.open(tempfilepath)

        print('Done.')


if __name__ == '__main__':
    main()
