#!/usr/bin/env python3

import argparse
import sys
import webbrowser
from html import escape
from pathlib import Path
from typing import NamedTuple

from lxml import html
from lxml.etree import _Element
from lxml.html import HtmlElement

from lawchecker import lawchecker_logger, templates
from lawchecker.amendment_document import Amendment, SupDocument
from lawchecker.amendment_similarity import (
    TextBucket,
    build_text_buckets,
    exact_duplicate_buckets,
    find_similar_pairs,
    group_by_location,
)
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, SIMILARITY_THRESHOLD
from lawchecker.utils import diff_xml_content


class DuplicateGroup(NamedTuple):
    text: str
    amendments: list[Amendment]


class LocationVariantGroup(NamedTuple):
    text: str  # shared text with the location prefix removed
    amendments: list[Amendment]


class SimilarGroup(NamedTuple):
    members_a: list[Amendment]
    members_b: list[Amendment]
    ratio: float
    html_diff: str | None


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
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ):
        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f'Error parsing HTML template file: {e}')
            raise

        self.sup_doc = SupDocument(xml_file)
        self.similarity_threshold = similarity_threshold

        self.duplicate_amendments: list[DuplicateGroup] = []
        self.similar_amendments: list[SimilarGroup] = []
        self.location_variants: list[LocationVariantGroup] = []

        # populate above lists of changes
        self.find_duplicates_and_similar()
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
                self.render_location_variants(),
                self.render_similar_amdts(),
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
            num_group = f'({", ".join([amdt.num for amdt in group.amendments])})'
            duplicate_numbers.append(num_group)

        duplicates_numbers_text = f'<p>{"<br>".join(duplicate_numbers)}</p>'

        card = templates.Card('Duplicate Amendments')
        card.secondary_info.extend(
            html.fragments_fromstring(
                f'{info}<p>{duplicates_content}</p>{duplicates_numbers_text}',
                no_leading_text=True,
            )
        )

        return card.html

    def render_location_variants(self) -> HtmlElement:
        info = (
            '<p><strong>Note:</strong> These amendments make the same change'
            ' at different locations: their text is identical once the leading'
            ' clause/schedule, page and line reference is removed. They are'
            ' excluded from the similar amendments check below.</p>'
        )
        intro = 'Groups of amendments with the same change at different locations:'
        count = (
            f'<strong>{len(self.location_variants)}</strong>'
            if self.location_variants
            else '<strong>None detected</strong>'
        )

        groups_html: list[str] = []
        for group in self.location_variants:
            nums = ', '.join(amdt.num for amdt in group.amendments)
            first_line = group.text.strip().split('\n')[0]
            groups_html.append(
                f'<p class="h5 mt-4">({escape(nums)})</p><p>{escape(first_line)}</p>'
            )

        card = templates.Card('Same Change at Different Locations', expanded=False)
        card.secondary_info.extend(
            html.fragments_fromstring(
                f'{info}<p>{intro} {count}</p>{"".join(groups_html)}',
                no_leading_text=True,
            )
        )

        return card.html

    def render_similar_amdts(self) -> HtmlElement:
        threshold_pct = round(self.similarity_threshold * 100)
        info = (
            '<p><strong>Note:</strong> Similar amendments are those which are'
            f' at least <strong>{threshold_pct}%</strong> similar in content'
            ' (and are not already exact duplicates). As with the duplicate'
            ' check, only the content of the amendments is considered.</p>'
        )
        sim_into = 'Pairs of similar amendments:'
        similar_content = f'{sim_into} <strong>None detected</strong>'

        if self.similar_amendments:
            similar_content = (
                f'{sim_into} <strong>{len(self.similar_amendments)}</strong>'
            )

        similar_html: list[str] = []
        for group in self.similar_amendments:
            nums_a = ', '.join(amdt.num for amdt in group.members_a)
            nums_b = ', '.join(amdt.num for amdt in group.members_b)
            similar_html.append(
                f'<p class="h5 mt-4">({nums_a}) and ({nums_b}):'
                f' {group.ratio:.1%} similar</p>'
            )
            if group.html_diff is not None:
                similar_html.append(group.html_diff)

        card = templates.Card('Similar Amendments')
        card.secondary_info.extend(
            html.fragments_fromstring(
                f'{info}<p>{similar_content}</p>{"".join(similar_html)}',
                no_leading_text=True,
            )
        )

        return card.html

    def find_duplicates_and_similar(self) -> None:
        buckets: list[TextBucket] = build_text_buckets(self.sup_doc.amendments)

        self.duplicate_amendments = [
            DuplicateGroup(text=bucket.normalized_text, amendments=bucket.members)
            for bucket in exact_duplicate_buckets(buckets)
        ]

        location_groups = group_by_location(buckets)

        self.location_variants = [
            LocationVariantGroup(
                text=group.bucket.normalized_text, amendments=group.bucket.members
            )
            for group in location_groups
            if group.variant_count > 1
        ]

        similar_pairs = find_similar_pairs(
            [group.bucket for group in location_groups],
            threshold=self.similarity_threshold,
        )

        for pair in similar_pairs:
            html_diff = diff_xml_content(
                pair.bucket_a.content_xml,
                pair.bucket_b.content_xml,
                fromdesc=pair.bucket_a.members[0].num,
                todesc=pair.bucket_b.members[0].num,
                normalise_spaces=False,
            )
            self.similar_amendments.append(
                SimilarGroup(
                    members_a=pair.bucket_a.members,
                    members_b=pair.bucket_b.members,
                    ratio=pair.ratio,
                    html_diff=html_diff,
                )
            )


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

    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=SIMILARITY_THRESHOLD,
        help=(
            'Minimum similarity ratio (0-1) for two amendments to be'
            f' reported as similar (default: {SIMILARITY_THRESHOLD})'
        ),
    )

    args = parser.parse_args(sys.argv[1:])

    filename = 'html_diff.html'

    report = Report(args.xml_doc, similarity_threshold=args.similarity_threshold)

    report.html_tree.write(
        filename,
        method='html',
        encoding='utf-8',
        doctype='<!DOCTYPE html>',
    )

    webbrowser.open(Path(filename).resolve().as_uri())


if __name__ == '__main__':
    main()
