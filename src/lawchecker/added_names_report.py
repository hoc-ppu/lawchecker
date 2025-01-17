#!/usr/bin/env python3

import argparse
import re
import shutil
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

from lawchecker import anr_post_processing_html, anr_spo_rest, settings
from lawchecker.lawchecker_logger import logger
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
        "--marshal",
        metavar="Folder",
        type=_dir_path,
        help="Optional Path to the folder containing the XML files "
        "(from LawMaker or FrameMaker) that you wish to use to marshal "
        "the report. Use quotes if there are spaces.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file name",
        default=settings.DEFAULT_OUTPUT_NAME,
    )

    args = parser.parse_args(sys.argv[1:])

    input_Path = Path(args.file.name)

    if args.marshal:
        marshal = Path(args.marshal)
    else:
        marshal = None

    run_xslts(
        input_Path,
        HTML_TEMPLATE,
        parameter=marshal,
        output_file_name=args.output,
    )


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


def run_xslts(
    input_Path: Path,
    parameter: Optional[Path] = None,
    output_file_name: str = settings.DEFAULT_OUTPUT_NAME,
):

    logger.info(f"{input_Path=} {parameter=}")

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
    logger.info(f"Resaved: {resave_Path}")

    # --- 1st Transformation - Intermediate XML ---
    logger.info("Running first transformation")
    anr_spo_rest.main(str(input_Path), str(intermediate_Path))

    # --- 2nd Transformation - HTML report ---
    logger.info("Running second transformation")
    anr_post_processing_html.main(
        str(HTML_TEMPLATE), str(intermediate_Path), str(parameter), str(out_html_Path)
    )

    # --- Finished Transforms ---
    logger.info(f"Created: {out_html_Path}")
    webbrowser.open(out_html_Path.as_uri())
    logger.info("Done.")


if __name__ == "__main__":
    main()
