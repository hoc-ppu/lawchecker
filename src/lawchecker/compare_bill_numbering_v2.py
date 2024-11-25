import re
import sys
from pathlib import Path
from typing import Iterable
import csv
from lxml import etree
from lxml.etree import _Element
from dateutil import parser as date_parser
import click

from lawchecker.lawchecker_logger import logger  # must be imported before any other

NSMAP = {
    "xmlns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
}

def clean(string: str, no_space=False, file_name_safe=False) -> str:
    # Some general cleaning
    string = string.casefold()
    string = re.sub(r"\s+", " ", string)
    string = string.replace(",", "")

    # Bill title cleaning
    string = string.replace("[hl]", "").strip()
    string = re.sub(r" bill$", "", string)

    if file_name_safe or no_space:
        string = string.replace(" ", "_")
        string = "".join(c for c in string if c.isalnum() or c == "_")

    return string.strip()


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
            stage = self.root.xpath(stage_xp, namespaces=NSMAP)[0]
            house = self.root.xpath(house_xp, namespaces=NSMAP)[0]
            return f"{house.replace('House of ', '')}, {stage}"
        except IndexError:
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
        secs_n_paras = self.root.xpath(xpath, namespaces=NSMAP)

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
    def __init__(self, xml_files: Iterable[tuple[_Element, str]]):
        self.bills_container = {}
        for xml_file in xml_files:
            try:
                bill = Bill(*xml_file)
                self.bills_container.setdefault(bill.title, []).append(bill)
            except IndexError as e:
                logger.error(f"Error parsing {xml_file[1]}: {repr(e)}")

    @classmethod
    # Get XML
    def from_folder(cls, in_folder: Path | None):
        in_folder = Path(in_folder or ".")
        xml_files = [(etree.parse(str(file)).getroot(), file.name) for file in in_folder.glob("*.xml")]
        return cls(xml_files)
    

    # Make the CSV
    def save_csv(self, out_folder: Path | None):
        out_folder = Path(out_folder or ".")
        for title, bills in self.bills_container.items():
            file_name = clean(title, file_name_safe=True) + ".csv"
            csv_path = out_folder / file_name
            with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Prepare headers
                headers = ["guid"] + [clean(bill.version, no_space=True) for bill in bills]
                writer.writerow(headers)

                # Prepare rows dictionary
                rows = {}
                for bill in bills:
                    sections = bill.get_sections()
                    guid_list = sections["guid"]
                    eid_list = sections[clean(bill.version, no_space=True)]

                    # Populate rows dictionary
                    for guid, eid in zip(guid_list, eid_list):
                        if guid not in rows:
                            rows[guid] = ["-"] * (len(headers) - 1)  # Initialize empty row
                        version_index = headers.index(clean(bill.version, no_space=True)) - 1
                        rows[guid][version_index] = eid

                # Write rows
                for guid, values in rows.items():
                    writer.writerow([guid] + values)

            print(f"Saved CSV: {csv_path}")

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