import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import click
from dateutil import parser as date_parser
from lxml import etree
from lxml.etree import _Element

from lawchecker.lawchecker_logger import logger
from lawchecker.templates import Table

NSMAP = {
    "xmlns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
}


def clean(string: str, no_space=False, file_name_safe=False) -> str:
    """
    Clean up a string for use in filenames or as a column header.
    """
    # Some general cleaning
    string = string.casefold()
    string = re.sub(r"\s+", " ", string)
    string = string.replace(",", "")

    # Bill title cleaning
    string = string.replace("[hl]", "").strip()
    string = re.sub(r" bill$", "", string)

    # Cleanup
    if file_name_safe or no_space:
        string = string.replace(" ", "_")
        string = "".join(c for c in string if c.isalnum() or c == "_")

    return string.strip()


@dataclass
class ComparisonTableContainer:
    bill_title: str
    headers: list[str]
    rows: list[list[str]]


class Bill:
    def __init__(self, bill_xml: _Element, file_name: str):
        self.root = bill_xml
        self.file_name = file_name
        self.version = self.get_version()
        self.title = self.get_bill_title()
        self.published_dt = self.get_published_date()

    def get_published_date(self) -> str | None:
        xpath = '//xmlns:FRBRManifestation/xmlns:FRBRdate[@name != "akn_xml"]/@date[not(.="")]'
        try:
            date_time: str = self.root.xpath(xpath, namespaces=NSMAP)[0]
            dt = date_parser.parse(date_time)
            return dt.strftime("%Y-%m-%d-%H-%M-%S")
        except Exception:
            logger.warning(f"Date not found in {self.file_name}")
            return None

    def get_version(self) -> str:
        xpath_temp = '//xmlns:references/*[@eId="{}"]/@showAs'
        stage_xp = xpath_temp.format("varStageVersion")
        house_xp = xpath_temp.format("varHouse")
        try:
            stage = self.root.xpath(stage_xp, namespaces=NSMAP)[0]  # type: ignore
            house = self.root.xpath(house_xp, namespaces=NSMAP)[0]  # type: ignore
            return f"{house.replace('House of ', '')}, {stage}"
        except IndexError:
            # if the above fails, we probably do not have a LM bill
            raise

    def get_bill_title(self) -> str:
        xpath = '//xmlns:TLCConcept[@eId="varBillTitle"]/@showAs'
        try:
            title: str = self.root.xpath(xpath, namespaces=NSMAP)[0]
            return clean(title)
        except Exception:
            logger.error(f"Bill title not found in {self.file_name}")
            sys.exit(1)

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

        for element in secs_n_paras:
            guid = element.get("GUID")
            eid = element.get("eId")
            if guid is None or eid is None:
                logger.warning("Section with no GUID or EID")
                continue
            attrs["guid"].append(guid)
            attrs[ref_col_name].append(re.sub(r"__oc_\d+", "", eid.split("__")[0]))

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
    def __init__(self, xml_files: Iterable[tuple[etree._Element, str]]):
        """Sorts all bills into a dictionary with the bill title as the key.
        The value is a list of Bill objects. So different versions of the same
        bill are grouped together."""

        self.bills_container = {}
        print("CompareBillNumbering initialized")

        # parse each bill and store in dictionary
        for xml_file in xml_files:
            try:
                bill = Bill(*xml_file)
                self.bills_container.setdefault(bill.title, []).append(bill)
                print(f"Bill added: {bill.title}")
            except IndexError as e:
                logger.error(f"Error parsing {xml_file[1]}: {repr(e)}")

    @classmethod
    def from_folder(cls, in_folder: Path | None):
        print(f"from_folder called with in_folder: {in_folder}")
        in_folder = Path(in_folder or ".")
        xml_files = []

        for xml_file_path in in_folder.glob("*.xml"):
            try:
                tree = etree.parse(str(xml_file_path))
                root = tree.getroot()
                xml_files.append((root, str(xml_file_path)))
                print(f"XML file parsed: {xml_file_path}")
            except etree.XMLSyntaxError as e:
                logger.error(f"Error parsing {xml_file_path}: {repr(e)}")
        print(f"Total XML files parsed: {len(xml_files)}")
        return cls(xml_files)

    def compare_bill(self):
        """
        Compare the numbering of bills and return the result.
        """
        print("compare_bill called")
        bill_comparison_dict = self._create_comparison_data()
        return bill_comparison_dict

    def _create_comparison_data(self) -> dict[str, dict[str, list]]:
        """
        Create a comparison dictionary similar to the pandas DataFrame output.
        Returns:
            A dictionary where:
                - keys are bill titles
                - values are dictionaries with "headers" (list of column headers)
                  and "rows" (list of row data)
        """
        bill_comparison_dict = {}
        print("Creating comparison data")
        for title, bills in self.bills_container.items():
            # If there are fewer than 2 bills, skip comparison
            if len(bills) < 2:
                logger.warning(f"Only one '{title}' bill found. Cannot compare.")
                continue

            # Sort bills by published date if available
            if all(bill.published_dt for bill in bills):
                bills.sort(key=lambda x: x.published_dt)

            # Initialize comparison structure
            headers = ["eid"] + [clean(bill.version, no_space=True) for bill in bills]
            rows = {}

            # Populate rows with eIds and corresponding data for each version
            for bill in bills:
                sections = bill.get_sections()
                eid_list = sections[clean(bill.version, no_space=True)]
                guid_list = sections["guid"]

                for guid, eid in zip(guid_list, eid_list):
                    if eid not in rows:
                        rows[eid] = ["-"] * (len(headers) - 1)  # Initialize row with placeholders
                    version_index = headers.index(clean(bill.version, no_space=True)) - 1
                    rows[eid][version_index] = guid  # Store GUID for this eId

            # Sort rows by eId
            sorted_rows = sorted(rows.items(), key=lambda x: self._get_sort_number(x[0]))

            # Store data for this bill
            bill_comparison_dict[title] = {
                "headers": headers,
                "rows": [[eid] + data for eid, data in sorted_rows]
            }
        print("Comparison data created")
        return bill_comparison_dict

    def _get_sort_number(self, eid: str) -> int:
        """Create a number from the digits in the eId for sorting."""
        digits = re.findall(r'\d+', eid)  # Extract digits from the eId
        if not digits:
            return 0  # If no digits are found, treat as zero for sorting
        return int("".join(d.zfill(3) for d in digits))  # Combine digits for sorting

    def _create_comparison_table_containers(self) -> list[ComparisonTableContainer]:

        comparison_tables = []

        for title, bills in self.bills_container.items():

            # Initialize comparison structure
            headers = ["guid"] + [clean(bill.version, no_space=True) for bill in bills]

            # Populate rows with eIds and corresponding data for each version
            rows = {}
            for bill in bills:
                sections = bill.get_sections()
                eid_list = sections[clean(bill.version, no_space=True)]
                guid_list = sections["guid"]

                for guid, eid in zip(guid_list, eid_list):
                    if guid not in rows:
                        rows[guid] = ["-"] * (len(headers) - 1)  # Initialize empty row

                    version_index = headers.index(clean(bill.version, no_space=True)) - 1
                    rows[guid][version_index] = eid

            comparison_tables.append(
                ComparisonTableContainer(
                    title, headers, [[guid] + values for guid, values in rows.items()]
                )
            )

        return comparison_tables

    # Make the CSV
    def save_csv(self, out_folder: Path | None):
        out_folder = Path(out_folder or ".")

        comparison_table_containers = self._create_comparison_table_containers()

        for comparison_table_container in comparison_table_containers:
            title = comparison_table_container.bill_title
            headers = comparison_table_container.headers

            file_name = clean(title, file_name_safe=True) + ".csv"
            csv_path = out_folder / file_name

            with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Prepare headers
                writer.writerow(headers)

                # Prepare rows
                for row in comparison_table_container.rows:
                    writer.writerow(row)

        print(f"Saved CSV: {csv_path}")

        # for title, bills in self.bills_container.items():
        #     file_name = clean(title, file_name_safe=True) + ".csv"
        #     csv_path = out_folder / file_name
        #     with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
        #         writer = csv.writer(csvfile)

        #         # Prepare headers
        #         headers = ["guid"] + [clean(bill.version, no_space=True) for bill in bills]
        #         writer.writerow(headers)

        #         # Prepare rows dictionary
        #         rows = {}
        #         for bill in bills:
        #             sections = bill.get_sections()
        #             guid_list = sections["guid"]
        #             eid_list = sections[clean(bill.version, no_space=True)]

        #             # Populate rows dictionary
        #             for guid, eid in zip(guid_list, eid_list):
        #                 if guid not in rows:
        #                     rows[guid] = ["-"] * (len(headers) - 1)  # Initialize empty row
        #                 version_index = headers.index(clean(bill.version, no_space=True)) - 1
        #                 rows[guid][version_index] = eid

        #         # Write rows
        #         for guid, values in rows.items():
        #             writer.writerow([guid] + values)

        #     print(f"Saved CSV: {csv_path}")


    def to_html_tables(self) -> list[etree._Element]:

        comparison_table_containers = self._create_comparison_table_containers()

        html_list = []

        for table in comparison_table_containers:
            table_html = Table(table.headers, table.rows).html

            # consider changing the below to return an etree.Element insted
            html_list.append(table_html)

        return html_list


# CLI
@click.command()
@click.option(
    '--input-folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Specify a different folder for finding bill XML. Defaults to current directory.",
)
@click.option(
    "--output-folder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help="Specify a different folder for saving the output files. Defaults to current directory.",
)
def cli(input_folder, output_folder):
    """
    Takes in UK bill XML files and generates CSV and HTML comparison reports.
    """
    input_folder = Path(input_folder or ".")
    output_folder = Path(output_folder or ".")
    compare = CompareBillNumbering.from_folder(input_folder)
    compare.save_csv(output_folder)


if __name__ == "__main__":
    cli()
