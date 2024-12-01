#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

# 3rd party saxon imports
# import saxonche

from lawchecker.lawchecker_logger import logger
from lawchecker import settings
from lawchecker.settings import HTML_TEMPLATE

def main():
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
            "File path to the XML you wish to process."
            " Use quotes if there are spaces."
        ),
    )

    parser.add_argument(
        "--xslts",
        metavar="XSLT Folder",
        type=_dir_path,
        help=(
            "Optional Path to the folder containing the XSLTs you wish to run."
            " Use quotes if there are spaces."
        ),
    )

    parser.add_argument(
        "--marshal",
        metavar="Folder",
        type=_dir_path,
        help="Optional Path to the folder containing the XML files "
        "(from LawMaker or FrameMaker) that you wish to use to marshal "
        "the report. Use quotes if there are spaces.",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file name",
        default=settings.DEFAULT_OUTPUT_NAME,
    )

    args = parser.parse_args(sys.argv[1:])

    input_Path = Path(args.file.name)

    if args.xslts:
        xsl_1_Path = Path(args.xslts) / settings.XSL_1_NAME
        xsl_2_Path = Path(args.xslts) / settings.XSL_2_NAME
    else:
        xsl_1_Path = settings.XSL_1_PATH
        xsl_2_Path = settings.XSL_2_PATH

    if args.marshal:
        marshal = Path(args.marshal)
    else:
        marshal = None

    run_xslts(
        input_Path,
        xsl_1_Path,
        xsl_2_Path,
        HTML_TEMPLATE,
        parameter=marshal,
        output_file_name=args.output
    )


def remove_docstring(parameter: Path):

    """
    Process FM XML files to remove docstring and overwrite original
    """

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

            # TODO: don't read the whole file into memory
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

        logger.info(f"Trying to remove docstring from {file.name}")

        # try to overwrite file
        with open(file, "w", encoding="UTF-8") as fi:
            # need to remove FM doctype
            # remove anything before the root element
            fi.writelines(file_lines[root_start:])


def extract_date(input_Path: Path) -> str:
    """Extract date form input XML from SharePoint"""

    with open(input_Path) as f:
        input_xml_str = f.read()

    # get the updated date
    match = re.search(r"(<updated>)([A-Z0-9:+-]+)(</updated>)", input_xml_str)
    date_str = ""
    if match:
        date_str = match.group(2)
        logger.info(f"Date extracted from input xml (from SharePoint) {date_str}")

    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        formated_date = dt.strftime("%Y-%m-%d__%H-%M")

    except Exception as e:
        logger.warning(f"Date not found in xml: {repr(e)}")
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
            logger.error("Error:", err_txt)
            # if USE_GUI:
            #     # this can be caught in the GUI code and the
            #     # Error message displayed in a GUI window
            #     raise Exception(err_txt) from e
            return False

    return True


def run_xslts(
    input_Path: Path,
    xsl_1_Path: Path,
    xsl_2_Path: Path,
    parameter: Optional[Path] = None,
    output_file_name: str = settings.DEFAULT_OUTPUT_NAME,
):
    logger.info(f"{input_Path=}   {xsl_1_Path=}   {xsl_2_Path=}   {parameter=}")

    xsls_exist = check_xsl_paths(xsl_1_Path, xsl_2_Path)
    if not xsls_exist:
        return

    formated_date = extract_date(input_Path)

    intermediate_file_name = f"{formated_date}_intermediate.xml"
    input_file_resave_name = f"{formated_date}_input_from_SP.xml"

    if settings.ANR_WORKING_FOLDER is None:
        dated_folder_Path = settings.REPORTS_FOLDER.joinpath(formated_date).resolve()
    else:
        dated_folder_Path = settings.ANR_WORKING_FOLDER.resolve()
    dated_folder_Path.mkdir(parents=True, exist_ok=True)

    xml_folder_Path = dated_folder_Path.joinpath(settings.DASHBOARD_DATA_FOLDER)
    xml_folder_Path.mkdir(parents=True, exist_ok=True)

    intermediate_Path = xml_folder_Path.joinpath(intermediate_file_name)
    out_html_Path = dated_folder_Path.joinpath(output_file_name)

    logger.info(f"{intermediate_Path=}   {out_html_Path=}")

    # Resave the input file
    resave_Path = xml_folder_Path.joinpath(input_file_resave_name)
    if input_Path != resave_Path:
        shutil.copy(input_Path, resave_Path)
    print(f"Resaved: {resave_Path}")

    # --- 1st Transformation (added-names-spo-rest) ---
    command_1 = ["python", str(xsl_1_Path), str(input_Path), str(intermediate_Path)]
    print(f"Initial command_1: {' '.join(command_1)}")
    logger.info(f"Running first transformation script: {xsl_1_Path}")
    logger.debug(f"Command 1: {' '.join(command_1)}")
    subprocess.run(command_1, check=True)

    # --- 2nd Transformation (post-processing-html) ---
    command_2 = ["python", str(xsl_2_Path), str(HTML_TEMPLATE), str(intermediate_Path), str(out_html_Path)]
    logger.debug(f"Initial command_2: {' '.join(command_2)}")
   
    logger.info(f"Running second transformation script: {xsl_2_Path}")
    logger.debug(f"Command 2: {' '.join(command_2)}")

    # Verify the length of command_2
    if len(command_2) < 5:
        logger.error(f"command_2 has insufficient arguments: {command_2}")
        raise IndexError("command_2 has insufficient arguments")

    subprocess.run(command_2, check=True)


    # --- finished transforms ---
    logger.info(f"Created: {out_html_Path}")
    webbrowser.open(out_html_Path.as_uri())
    logger.info("Done.")

    return command_1, command_2

if __name__ == "__main__":
    main()
