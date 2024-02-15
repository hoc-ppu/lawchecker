import re
import sys
from pathlib import Path
from typing import Iterable

import click
import pandas as pd
from dateutil import parser as date_parser
from lxml import etree
from lxml.etree import _Element
from pandas import Series

from supcheck.supcheck_logger import logger  # must be imported before any other

NSMAP = {
    "xmlns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
}


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

    CompareBillNumbering.from_folder(input_folder).save_csv(output_folder)


# ------------------------ Begin main program ------------------------ #

class Bill:

    def __init__(self, bill_xml: _Element, file_name: str):

        # self.root = etree.parse(str(file)).getroot()
        self.root = bill_xml

        # self.file = file
        self.file_name = file_name
        self.version = self.get_version()
        self.title = self.get_bill_title()
        self.published_dt = self.get_published_date()

    def get_published_date(self) -> str | None:

        xpath = '//xmlns:FRBRManifestation/xmlns:FRBRdate[@name != "akn_xml"]/@date[not(.="")]'

        try:
            date_time: str = self.root.xpath(xpath, namespaces=NSMAP)[0]  # type: ignore
            dt = date_parser.parse(date_time)
            formatted = dt.strftime("%Y-%m-%d-%H-%M-%S")

        except Exception:
            # logger.error(f"Date not found in {self.file.name}")
            logger.warning(f"Date not found in {self.file_name}")
            return None

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
            # logger.error(f"Bill title not found in {self.file.name}")
            logger.error(f"Date not found in {self.file_name}")
            sys.exit(1)

        title = clean(title)

        return title

    def get_sections(self):

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

        secs_n_paras: list[etree._Element] = self.root.xpath(xpath, namespaces=NSMAP)  # type: ignore

        if len(secs_n_paras) == 0:
            logger.warning("No sections or paragraphs found")

        for element in secs_n_paras:

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

class CompareBillNumbering:
    def __init__(self, xml_files: Iterable[tuple[_Element, str]]):

        # Sort all bills into a dictionary with the bill title as the key.
        # The value is a list of Bill objects. So different versions of the same
        # bill are grouped together.

        self.bills_container = {}

        # parse each bill and store in dictionary
        for xml_file in xml_files:

            logger.info(f"file_name: {xml_file[1]}")

            bill = Bill(*xml_file)

            if bill.title not in self.bills_container:
                self.bills_container[bill.title] = [bill]
            else:
                self.bills_container[bill.title].append(bill)

        self.bill_comparison_dict: dict[str, pd.DataFrame] = self._create_comparison_df()

    @classmethod
    def from_folder(cls, in_folder: Path | None):
        if in_folder is None:
            in_folder = Path(".")
        else:
            in_folder = in_folder

        logger.info(f"Folder path: {in_folder.resolve()}")

        # get all the XML files in the input folder
        xml_files = in_folder.glob("*.xml")

        xml_files2 = [(etree.parse(str(file)).getroot(), file.name) for file in xml_files]

        return CompareBillNumbering(xml_files2)


    def _create_comparison_df(self) -> dict[str, pd.DataFrame]:

        bill_comparison_dict: dict[str, pd.DataFrame] = {}

        df = pd.DataFrame()  # empty dataframe

        for title, bills in self.bills_container.items():

            # if there is less than 2 bills, we can't compare them
            if len(bills) < 2:
                logger.warning(f"Only one '{title}' bill found. Cannot compare.")
                continue

            if not all(bill.published_dt for bill in bills):
                logger.warning("Published date not found for all bills. Bills may note be ordered correctly.")
            else:
                bills.sort(key=lambda x: x.published_dt)  # sort by published date

            data_frames: list[pd.DataFrame] = []

            for bill in bills:

                # get the sections, store in a dataframe
                df = pd.DataFrame(bill.get_sections())

                # add col for later sorting
                df['order'] = df.apply(get_sort_number, axis=1)

                data_frames.append(df)

            # outer join all dataframes
            df = data_frames[0]
            for i, x in enumerate(data_frames[1:]):
                # suffixes are added to column names to avoid collision when joining
                df = df.merge(x, how="outer", on='guid', suffixes=(f"_{i}l", f"_{i}r"))


            # Need to sort rows as (sadly) an outer join doesn't keep the order.

            # get the ordering columns (suffixes are added during join)
            order_cols = [col for col in df.columns if col.startswith("order")]

            # add master order column with mean order (NaN not included in mean)
            df['order_master'] = df[order_cols].mean(axis=1)
            order_cols.append('order_master')

            df.sort_values(by='order_master', inplace=True)

            # remove the order columns
            df.drop(columns=order_cols, inplace=True)

            bill_comparison_dict[title] = df

        return bill_comparison_dict

    def save_csv(self, out_folder: Path | None) -> list[Path]:

        saved_csv_files: list[Path] = []

        for title, df in self.bill_comparison_dict.items():

            csv_file_name = f"{clean(title, file_name_safe=True)}.csv"

            if out_folder is not None:
                csv_file_name = out_folder / csv_file_name
            else:
                csv_file_name = Path(csv_file_name)

            df.to_csv(csv_file_name, index=False)

            saved_csv_files.append(csv_file_name)

            msg = f"Saved: {csv_file_name.resolve()}"
            logger.info(msg)
            print(msg)

        print("Done")
        return saved_csv_files

    def to_html(self) -> list[str]:

        html_list = []

        for _, df in self.bill_comparison_dict.items():

            html = df.to_html(
                index=False,
                na_rep='-',  # replace NaN with a dash
                justify="left",
                classes=("sticky-head", "table-responsive-md", "table")
            )
            # print(html)
            html_list.append(html)

        return html_list



# ------------------------ Begin helper functions ------------------------ #

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
