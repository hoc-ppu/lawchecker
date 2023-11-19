import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import click
import pandas as pd
from dateutil import parser as date_parser
from lxml import etree
from lxml.etree import _Element
from pandas import Series

NSMAP = {
    "xmlns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
}


# --------------------------- BEGIN LOGGER --------------------------- #

logger = logging.getLogger('renumbered')
logger.setLevel(logging.DEBUG)

log_file_Path = Path(Path.home(), 'logs', 'renumbered.log').absolute()
log_file_Path.parent.mkdir(parents=True, exist_ok=True)

# create file handler which logs even debug messages
fh = RotatingFileHandler(str(log_file_Path), mode='a', maxBytes=1024 * 1024)
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()  # create console handler
ch.setLevel(logging.WARNING)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to the handler(s)
ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(ch)  # add the handler to the logger
logger.addHandler(fh)

# -------------------- Begin comand line interface ------------------- #

@click.command()
@click.option(
    '--input-folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Specify a different folder for finding bill XML."
         " Defaults to current directory.",
)
@click.option(
    "--output-folder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help="Specify a different folder for saving the output CSV file(s) in."
         " Defaults to current directory.",
)
def cli(input_folder, output_folder):

    """
    Takes in a UK bill XML files. Return CSV file(s) comparing
    the numbering of each version of the same bill.
    """

    if input_folder is not None:
        input_folder = Path(input_folder)
    if output_folder is not None:
        output_folder = Path(output_folder)

    compare_bills(input_folder, output_folder)


# ------------------------ Begin main program ------------------------ #

class Bill:

    def __init__(self, file: Path):

        self.root = etree.parse(str(file)).getroot()

        self.file = file
        self.version = self.get_version()
        self.title = self.get_bill_title()
        self.published_dt = self.get_published_date()

    def get_published_date(self) -> str:

        xpath = '//xmlns:FRBRManifestation/xmlns:FRBRdate[@name != "akn_xml"]/@date[not(.="")]'

        try:
            date_time: str = self.root.xpath(xpath, namespaces=NSMAP)[0]  # type: ignore
            dt = date_parser.parse(date_time)
            formatted = dt.strftime("%Y-%m-%d-%H-%M-%S")

        except Exception:
            logger.error(f"Date not found in {self.file.name}")
            sys.exit(1)

        return formatted

    def get_version(self) -> str:

        xpath_temp = '//xmlns:references/*[@eId="{}"]/@showAs'
        stage_xp = xpath_temp.format("varStageVersion")
        house_xp = xpath_temp.format("varHouse")

        stage: str = self.root.xpath(stage_xp, namespaces=NSMAP)[0]  # type: ignore
        house: str = self.root.xpath(house_xp, namespaces=NSMAP)[0]  # type: ignore

        house = house.replace("House of ", "")

        return f"{house}, {stage}"

    def get_bill_title(self) -> str:

        xpath = '//xmlns:TLCConcept[@eId="varBillTitle"]/@showAs'
        try:
            title: str = self.root.xpath(xpath, namespaces=NSMAP)[0]  # type: ignore
            assert isinstance(title, str)
        except Exception:
            logger.error(f"Bill title not found in {self.file.name}")
            sys.exit(1)

        title = clean(title)

        return title

    def get_sections(self):

        # sort_order_col_name = f"order_{self.published_dt}"
        ref_col_name = clean(self.version, no_space=True)

        # ref_col_name will contain eId
        attrs = {"guid": [], ref_col_name: []}

        xpath = (
            "//xmlns:body//xmlns:section"          # sections
            "[not(contains(@eId, 'subsec')) "      # skip subsections
            "and not(contains(@eId, 'qstr'))]"     # skip qstr elements
            "|//xmlns:body//xmlns:paragraph"       # paragraphs
            "[contains(@eId, 'sched') "            # only keep the schedules
            "and not(contains(@eId, 'subpara')) "  # remove subpara
            "and not(contains(@eId, 'qstr'))]"     # and qstr (duplicated)
        )

        sections_paragraphs: list[_Element] = self.root.xpath(xpath, namespaces=NSMAP)  # type: ignore

        if len(sections_paragraphs) == 0:
            logger.warning("No sections or paragraphs found")

        for element in sections_paragraphs:

            guid = element.get('GUID', None)
            eid = element.get('eId', None)

            if guid is None or eid is None:
                logger.warning("Section with no GUID or EID")
                continue

            element_name = etree.QName(element).localname

            if element_name == "section":

                # and oc notations (duplicated)
                # I think here we are supposed to edit the eid value
                # to remove '__' and anything after it
                eid = eid.split("__")[0]

            if element_name == "paragraph":

                # remove oc notations
                # (__oc_#, sometimes at end and sometimes middle of string)
                eid = re.sub(r"__oc_\d+", "", eid)

            attrs[ref_col_name].append(eid)
            attrs["guid"].append(guid)

        return attrs


def compare_bills(in_folder: Path | None, out_folder: Path | None) -> None:

    if in_folder is None:
        in_folder = Path(".")  # use current directory

    logger.info(f"Folder path: {in_folder.resolve()}")

    # get all the XML files
    xml_files = in_folder.glob("*.xml")

    bills_container: dict[str, list[Bill]] = {}

    for xml_file in xml_files:

        # parse bills and sort into dictionary with bill title as key

        logger.info(f"{xml_file=}")

        bill = Bill(xml_file)

        if bill.title not in bills_container:
            bills_container[bill.title] = [bill]
        else:
            bills_container[bill.title].append(bill)

    # all bills are now sorted into a dictionary with the bill title as the key.
    # The value is a list of Bill objects. So different versions of the same
    # bill are grouped together.

    # we should further order the list of bills by the published date
    for title, bills in bills_container.items():

        # if there is less than 2 bills, we can't compare them
        if len(bills) < 2:
            logger.warning(f"Only one '{title}' bill found. Cannot compare.")
            continue

        bills.sort(key=lambda x: x.published_dt)  # sort by published date

        data_frames: list[pd.DataFrame] = []

        for bill in bills:

            # get the sections, store in a dataframe
            df = pd.DataFrame(bill.get_sections())

            # add col for later sorting
            df['order'] = df.apply(get_sort_number, axis=1)

            data_frames.append(df)

        df = data_frames[0]

        for i, x in enumerate(data_frames[1:]):
            # outer join all dataframes
            # suffixes are added to column names to avoid collision when joining
            df = df.merge(x, how="outer", on='guid', suffixes=(f"_{i}l", f"_{i}r"))

        # Need to sort rows as, sadly, an outer join doesn't keep the order.

        # get the ordering columns (suffixes are added during join)
        order_cols = [col for col in df.columns if col.startswith("order")]

        # add master order column with mean order (NaN not included in mean)
        df['order_master'] = df[order_cols].mean(axis=1)
        order_cols.append('order_master')

        df.sort_values(by=['order_master'], inplace=True)

        # remove the order columns
        df.drop(columns=order_cols, inplace=True)

        file_name = f"{clean(title, file_name_safe=True)}_compare.csv"

        if out_folder is not None:
            file_name = out_folder / file_name
        else:
            file_name = Path(file_name)

        df.to_csv(file_name, index=False)

        msg = f"Saved {file_name.resolve()}"
        logger.info(msg)
        print(msg)

    print("Done")



def get_sort_number(row: Series) -> int:

    """Create a number from the digits in the eId for sorting."""

    # assumption! eId is always in position 1
    digits = re.findall(r'\d+', row.iloc[1])

    # pad with zeros and concatenate
    string = "".join(x.zfill(3) for x in digits)

    try:
        return int(string)
    except ValueError:
        return 0  # problem so put these at the top



def clean(string: str, no_space=False, file_name_safe=False) -> str:

    # some general cleaning
    string = string.casefold()  # makes lowercase and removes accents
    string = re.sub(r"\s+", " ", string)
    string = string.replace(",", "")

    # bill title cleaning
    string = string.replace("[hl]", "").strip()
    string = re.sub(r" bill$", "", string)

    # I don't like spaces in file names 😛
    if file_name_safe:
        no_space = True

    if no_space:
        # replace spaces with underscores
        string = string.replace(" ", "_")

    if file_name_safe:
        keep = ("_")
        string = "".join(c for c in string if c.isalnum() or c in keep)

    return string.strip()


if __name__ == "__main__":
    cli()
