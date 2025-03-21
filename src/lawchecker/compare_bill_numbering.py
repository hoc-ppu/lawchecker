import argparse
import csv
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lxml import etree
from lxml.etree import _Element
from lxml.html import HtmlElement

from lawchecker.lawchecker_logger import logger
from lawchecker.templates import Table

NSMAP = {
    'xmlns': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'ukl': 'https://www.legislation.gov.uk/namespaces/UK-AKN',
}

LIKELY_DATE_FORMATS = [
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M:%S%z',
]


def clean(string: str, no_space=False, file_name_safe=False) -> str:
    """
    Clean up a string for use in filenames or as a column header.
    """
    # Some general cleaning
    string = string.casefold()
    string = re.sub(r'\s+', ' ', string)
    string = string.replace(',', '')

    # Bill title cleaning
    string = string.replace('[hl]', '').strip()
    string = re.sub(r' bill$', '', string)

    # Cleanup
    if file_name_safe or no_space:
        string = string.replace(' ', '_')
        string = ''.join(c for c in string if c.isalnum() or c == '_')

    return string.strip()


@dataclass
class ComparisonTableContainer:
    bill_title: str
    headers: list[str]
    rows: list[list[str]]


def try_parse_date(
    date_str: str, date_formats: list[str] = LIKELY_DATE_FORMATS
) -> datetime | None:
    date_str = date_str.strip()

    # sometimes dates follow the ISO 8601 standard so try that first
    if date_str.endswith('Z'):
        date_str = date_str[:-1] + '+00:00'
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            pass

    for date_format in date_formats:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    return None


class Bill:
    def __init__(self, bill_xml: _Element, file_name: str):
        self.root = bill_xml
        self.file_name = file_name
        self.version = self.get_version()
        self.title = self.get_bill_title()
        self.published_dt = self.get_published_date()

    def get_published_date(self) -> str:
        xpath = '//xmlns:FRBRManifestation/xmlns:FRBRdate[@name != "akn_xml"]/@date[not(.="")]'

        try:
            dt = try_parse_date(self.root.xpath(xpath, namespaces=NSMAP)[0])

            if not dt:
                raise Exception('Date not found')

        except Exception:
            logger.warning(f'Date not found in {self.file_name}')
            return datetime.max.strftime('%Y-%m-%d-%H-%M-%S')
        else:
            return dt.strftime('%Y-%m-%d-%H-%M-%S')

    def get_version(self) -> str:
        xpath_temp = '//xmlns:references/*[@eId="{}"]/@showAs'
        stage_xp = xpath_temp.format('varStageVersion')
        house_xp = xpath_temp.format('varHouse')
        try:
            stage = self.root.xpath(stage_xp, namespaces=NSMAP)[0]  # type: ignore
            house = self.root.xpath(house_xp, namespaces=NSMAP)[0]  # type: ignore
            return f'{house.replace("House of ", "")}, {stage}'
        except IndexError:
            # if the above fails, we probably do not have a LM bill
            raise

    def get_bill_title(self) -> str:
        xpath = '//xmlns:TLCConcept[@eId="varBillTitle"]/@showAs'
        try:
            title: str = self.root.xpath(xpath, namespaces=NSMAP)[0]
            return clean(title)
        except Exception:
            logger.error(f'Bill title not found in {self.file_name}')
            sys.exit(1)

    def get_sections(self):
        ref_col_name = clean(self.version, no_space=True)
        # ref_col_name will contain eId
        attrs = {'guid': [], ref_col_name: []}

        xpath = (
            '//xmlns:body//xmlns:section'  # sections
            "[not(contains(@eId, 'subsec')) "  # skip subsections
            "and not(contains(@eId, 'qstr'))]"  # skip qstr elements
            '|//xmlns:body//xmlns:paragraph'  # paragraphs
            "[contains(@eId, 'sched') "  # only keep the schedules
            "and not(contains(@eId, 'subpara')) "  # remove subpara
            "and not(contains(@eId, 'qstr'))]"  # and qstr (duplicated)
        )
        secs_n_paras: list[etree._Element] = self.root.xpath(xpath, namespaces=NSMAP)  # type: ignore

        for element in secs_n_paras:
            guid = element.get('GUID')
            eid = element.get('eId')
            if guid is None or eid is None:
                logger.warning('Section with no GUID or EID')
                continue
            attrs['guid'].append(guid)
            attrs[ref_col_name].append(re.sub(r'__oc_\d+', '', eid.split('__')[0]))

        if len(secs_n_paras) == 0:
            logger.warning('No sections or paragraphs found')

        for element in secs_n_paras:
            guid = element.get('GUID', None)
            eid = element.get('eId', None)

            if guid is None or eid is None:
                logger.warning('Section with no GUID or EID')
                continue

            element_name = etree.QName(element).localname

            if element_name == 'section':
                # and oc notations (duplicated)
                # I think here we are supposed to edit the eid value
                # to remove '__' and anything after it
                eid = eid.split('__')[0]

            if element_name == 'paragraph':
                # remove oc notations
                # (__oc_#, sometimes at end and sometimes middle of string)
                eid = re.sub(r'__oc_\d+', '', eid)

            attrs[ref_col_name].append(eid)
            attrs['guid'].append(guid)

        return attrs


class CompareBillNumbering:
    def __init__(self, xml_files: Iterable[tuple[etree._Element, str]]):
        """Sorts all bills into a dictionary with the bill title as the key.
        The value is a list of Bill objects. So different versions of the same
        bill are grouped together."""

        self.bills_container: dict[str, list[Bill]] = {}
        logger.info('CompareBillNumbering initialized')

        # parse each bill and store in dictionary
        for xml_file in xml_files:
            try:
                bill = Bill(*xml_file)
                self.bills_container.setdefault(bill.title, []).append(bill)
                logger.info(f'Bill added: {bill.title}')
            except IndexError as e:
                logger.error(f'Error parsing {xml_file[1]}: {repr(e)}')

    @classmethod
    def from_folder(cls, in_folder: Path | None):
        """
        Create an instance of CompareBillNumbering by parsing all XML
        files in the specified folder.

        This method scans the specified folder for XML files, parses each file,
        and initializes a CompareBillNumbering instance with the parsed XML data.

        Parameters:
        in_folder (Path | None): The folder containing the XML files to be parsed.
                                 If None, the current directory is used.

        Returns:
        CompareBillNumbering: An instance of CompareBillNumbering.

        Raises:
        etree.XMLSyntaxError: If an XML file cannot be parsed due to syntax errors.
        """

        logger.info(f'from_folder called with in_folder: {in_folder}')
        in_folder = Path(in_folder or '.')
        xml_files = []

        for xml_file_path in in_folder.glob('*.xml'):
            try:
                tree = etree.parse(str(xml_file_path))
                root = tree.getroot()
                xml_files.append((root, str(xml_file_path)))
                logger.info(f'XML file parsed: {xml_file_path}')
            except etree.XMLSyntaxError as e:
                logger.error(f'Error parsing {xml_file_path}: {repr(e)}')
        logger.info(f'Total XML files parsed: {len(xml_files)}')
        return cls(xml_files)

    def _get_sort_number(self, eid: str) -> int:
        """Create a number from the digits in the eId for sorting."""

        digits = re.findall(r'\d+', eid)  # Extract digits from the eId
        if not digits:
            return 0  # If no digits are found, treat as zero for sorting
        return int(''.join(d.zfill(3) for d in digits))  # Combine digits for sorting

    def _create_comparison_table_containers(self) -> list[ComparisonTableContainer]:
        comparison_tables = []

        for title, bills in self.bills_container.items():
            # If there are fewer than 2 bills, skip comparison
            if len(bills) < 2:
                logger.warning(f"Only one '{title}' bill found. Cannot compare.")
                continue

            if all(bill.published_dt for bill in bills):
                bills.sort(key=lambda x: x.published_dt)
            else:
                logger.warning(
                    f"Published date not found for some files for '{title}'."
                    ' Output will not be ordered properly.'
                )

            # Initialize comparison structure
            headers = ['guid'] + [clean(bill.version, no_space=True) for bill in bills]

            # Populate rows with eIds and corresponding data for each version
            rows: dict[str, list[str]] = {}
            for bill in bills:
                sections = bill.get_sections()
                eid_list = sections[clean(bill.version, no_space=True)]
                guid_list = sections['guid']

                for guid, eid in zip(guid_list, eid_list):
                    if guid not in rows:
                        rows[guid] = ['-'] * (len(headers) - 1)  # Initialize empty row

                    version_index = (
                        headers.index(clean(bill.version, no_space=True)) - 1
                    )
                    rows[guid][version_index] = eid

            # sor the rows by eId
            rows_list = [[guid] + values for guid, values in rows.items()]
            rows_list.sort(
                key=lambda row: max(
                    self._get_sort_number(item) for item in row[1:] if item != '-'
                )
            )

            comparison_tables.append(
                ComparisonTableContainer(title, headers, rows_list)
            )

        return comparison_tables

    # Make the CSV
    def save_csv(self, out_folder: Path | None) -> list[Path]:
        out_folder = Path(out_folder or '.')

        created_csv_files: list[Path] = []

        comparison_table_containers = self._create_comparison_table_containers()

        for comparison_table_container in comparison_table_containers:
            title = comparison_table_container.bill_title
            headers = comparison_table_container.headers

            file_name = clean(title, file_name_safe=True) + '.csv'
            csv_path = out_folder / file_name

            with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Prepare headers
                writer.writerow(headers)

                # Prepare rows
                for row in comparison_table_container.rows:
                    writer.writerow(row)

                logger.info(f'Saved CSV: {csv_path}')

            created_csv_files.append(csv_path)

        return created_csv_files

    def to_html_tables(self) -> list[HtmlElement]:
        comparison_table_containers = self._create_comparison_table_containers()

        html_list: list[HtmlElement] = []

        for table in comparison_table_containers:
            table_html = Table(table.headers, table.rows).html

            # consider changing the below to return an etree.Element insted
            html_list.append(table_html)

        return html_list


def cli():
    parser = argparse.ArgumentParser(
        description=(
            'Takes in UK Bill XML files and generates CSV files(s)'
            ' showing how numbering (of clauses etc.) has changed.'
        )
    )

    parser.add_argument(
        '--input-folder',
        type=Path,
        help=(
            'Specify a different folder for finding bill XML.'
            ' Defaults to current directory.'
        ),
    )

    parser.add_argument(
        '--output-folder',
        type=Path,
        help=(
            'Specify a different folder for saving the output files.'
            ' Defaults to current directory.'
        ),
    )

    args = parser.parse_args(sys.argv[1:])

    print(repr(args))

    input_folder = Path(args.input_folder or '.')
    output_folder = Path(args.output_folder or '.')
    compile_ = CompareBillNumbering.from_folder(input_folder)
    compile_.save_csv(output_folder)


if __name__ == '__main__':
    cli()
