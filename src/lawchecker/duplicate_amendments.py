#!/usr/bin/env python3

import argparse
import re
import sys
import webbrowser
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from lxml import etree, html
from lxml.etree import QName, _Element
from lxml.html import HtmlElement

from lawchecker import lawchecker_logger, templates
from lawchecker import xpath_helpers as xp
from lawchecker.compare_amendment_documents import Amendment, SupDocument
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, NSMAP, PARSER, UKL
from lawchecker.utils import diff_xml_content, find_duplicates

# TODO: consider taking out of compare_amendment_documents.py Amendment and
# SupDocument classes and putting them in a separate module for shared use


class ChangedNames(NamedTuple):
    num: str
    added: list[str]
    removed: list[str]


class ChangedAmdt(NamedTuple):
    num: str
    html_diff: str


class DuplicateGroup(NamedTuple):
    text: str
    amendments: list[Amendment]


class Report:
    """
    Container for Amendment Report.
    The report summarises changes changes between two LM XML official list documents.
    There are assumed to be no published documents between the two documents,
    if there are then the star check will be inaccurate
    """

    def __init__(
        self,
        xml_file: Path | _Element,
    ):
        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f'Error parsing HTML template file: {e}')
            raise

        self.sup_doc = SupDocument(xml_file)

        self.duplicate_amendments: list[DuplicateGroup] = []

        # populate above lists of changes
        self.find_duplicates()
        # build up the html document
        self.make_html()  # this does not save the html document

    def make_html(self):
        """
        Build up HTML document with various automated checks on amendments
        """
        xp = './/div[@id="content-goes-here"]'
        insert_point: HtmlElement = self.html_root.find(xp)  # type: ignore
        # print(etr)
        insert_point.extend(
            (
                self.render_intro(),
                self.render_duplicate_amdts(),
            )
        )

    def render_intro(self) -> HtmlElement:
        # ------------------------- intro section ------------------------ #
        into = (
            'This report highlights any duplicate amendments in a LawMaker'
            ' XML official list document. The document is:'
            f'<br><strong>{self.sup_doc.file_name}</strong>'
        )

        meta_data_table = templates.Table(
            (
                '',
                self.sup_doc.file_name,
            )
        )

        meta_data_table.add_row(('File path', self.sup_doc.file_path))
        meta_data_table.add_row(('Bill Title', self.sup_doc.meta_bill_title))
        meta_data_table.add_row(('Published date', self.sup_doc.meta_pub_date))
        meta_data_table.add_row(('List Type', self.sup_doc.meta_list_type))

        section = html.fromstring(
            '<div class="wrap">'
            '<section id="intro">'
            '<h2>Introduction</h2>'
            f'<p>{into}</p>'
            '</section>'
            '</div>'
        )

        section.append(meta_data_table.html)

        return section

    def render_duplicate_amdts(self) -> HtmlElement:
        info = (
            '<p><strong>Note:</strong> When testing for duplicate amendments'
            ', only the content of the amendments is considered, not the'
            ' sponsor(s) or explanatory statement.<br>'
            'White space and structural differences in the XML are ignored.</p>'
        )
        dup_into = 'Amendments with one or more duplicates:'
        duplicates_content = f'{dup_into} <strong>None detected</strong>'

        if self.duplicate_amendments:
            duplicates_content = (
                f'{dup_into} <strong>{len(self.duplicate_amendments)}</strong>'
            )

        duplicate_numbers: list[str] = []
        for group in self.duplicate_amendments:
            # logger.info([amdt.num for amdt in group.amendments])
            num_group = f'({", ".join([amdt.num for amdt in group.amendments])})'
            duplicate_numbers.append(num_group)

        # logger.info(f'Duplicate numbers: {duplicate_numbers}')

        duplicates_numbers_text = f'<p>{"<br>".join(duplicate_numbers)}</p>'

        card = templates.Card('Duplicate Amendments')
        card.secondary_info.extend(
            html.fragments_fromstring(
                f'{info}<p>{duplicates_content}</p>{duplicates_numbers_text}',
                no_leading_text=True,
            )
        )

        return card.html

    def find_duplicates(self) -> None:
        bucket: dict[str, list[Amendment]] = {}

        # amdt_nums = [amdt.num for amdt in self.sup_doc.amendments]
        # logger.info(f'{amdt_nums=}')

        for amdt in self.sup_doc.amendments:
            contains_clauses_of_interest = False

            amdt_content = xp.get_amdt_content(amdt.xml)

            if len(amdt_content) == 0:
                logger.warning(f'{amdt.num}: has no content')
                continue

            amdt_content = deepcopy(amdt_content[0])

            # remove the num element as this will usually be changed between amendments
            amendment_num = amdt_content.find(
                './/xmlns:num[@ukl:dnum]', namespaces=NSMAP
            )

            stringy_num = etree.tostring(amdt_content, encoding=str) or ''
            if any(x in stringy_num for x in ('NC37', 'NC16')):
                contains_clauses_of_interest = True
                logger.info(etree.tostring(amdt_content, encoding=str))

            try:
                amendment_num.getparent().remove(amendment_num)
            except Exception as e:
                logger.info(f'Failed to remove amendment num: {e}')

            # we could use clean_lm_xml_amdt here but we won't for now

            text = xp.text_content(amdt_content)
            normalized_text = re.sub(r'\s+', '', text)
            normalized_text = re.sub(r'\n+', '', normalized_text)

            if contains_clauses_of_interest:
                logger.info(f'{normalized_text=}')

            if normalized_text in bucket:
                bucket[normalized_text].append(amdt)
            else:
                bucket[normalized_text] = [amdt]

        # Filter out entries that are not duplicates
        self.duplicate_amendments = [
            DuplicateGroup(text=text, amendments=amendments)
            for text, amendments in bucket.items()
            if len(amendments) > 1
        ]


def main():
    lawchecker_logger.setup_lawchecker_logging()
    parser = argparse.ArgumentParser(
        description=('Create an HTML document highlighting duplicate amendments.')
    )

    parser.add_argument(
        'xml_doc',
        type=Path,
        help='Amendment paper XML file to check for duplicates',
    )

    args = parser.parse_args(sys.argv[1:])

    filename = 'html_diff.html'

    report = Report(args.xml_doc)

    report.html_tree.write(
        filename,
        method='html',
        encoding='utf-8',
        doctype='<!DOCTYPE html>',
    )

    webbrowser.open(Path(filename).resolve().as_uri())


if __name__ == '__main__':
    main()
