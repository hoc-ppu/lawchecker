#!/usr/bin/env python3

import argparse
import sys
import webbrowser
from collections.abc import Sequence
from html import escape
from pathlib import Path
from typing import NamedTuple

from lxml import html
from lxml.etree import _Element
from lxml.html import HtmlElement

from lawchecker import lawchecker_logger, templates
from lawchecker import xpath_helpers as xp
from lawchecker.amendment_document import Amendment, Heading, SupDocument
from lawchecker.lawchecker_logger import logger
from lawchecker.marshalling import Alignment, Item, align
from lawchecker.settings import COMPARE_REPORT_TEMPLATE
from lawchecker.stars import BLACK_STAR, NO_STAR, WHITE_STAR
from lawchecker.utils import diff_xml_content, find_duplicates

# TODO: [x] put all sections in HTML document
# Add messages for Nil return
# [x] make ANR respect omit-from-report setting
# [x] put logger in separate file
# warn about problem amendments in an error section
# [x] error if input file is not XML
# warn if no amendments found
# [] pytest metadata
# [x] Rearange total counts to be at the top
# [x] shorten class Xpath
# put duplicate names back in output – not necessary as LM deduplicates names
# test on more example documents
# [x] warn if bill titles don't match
# [] warn if old XML file and new XML file seem to be the wrong way around,
#   i.e. if the old file seems newer than the new  file.
# think about changing 1 to A1 or Amendment 1... to make it look better in
# Added and removed amendments. See
# check_amendments.py LM_XML/digital_rm_rep_0825.xml LM_XML/digital_rm_rep_0906.xml


class ChangedNames(NamedTuple):
    num: str
    added: list[str]
    removed: list[str]


class ChangedAmdt(NamedTuple):
    num: str
    html_diff: str


class PaperWarning(NamedTuple):
    """A reason the two papers may not be comparable"""

    summary: str  # one sentence
    detail: str
    # True when the papers are known to differ (different stages or bills).
    # False when the check could not be done (the metadata is missing).
    papers_differ: bool = False


def check_papers_match(
    old_doc: SupDocument, new_doc: SupDocument
) -> list[PaperWarning]:
    """
    Check that the two papers are from the same stage of the same bill.

    Amendment numbers start again at each stage, so on papers from different
    stages the same number usually means a different amendment, and the
    rest of the report compares the wrong amendments. These are warnings
    only: the report is still made. If the metadata needed is missing from
    either paper, the warning says that the check could not be done.
    """

    def same(old_value: str, new_value: str) -> bool:
        # ignore differences in case and spacing
        return old_value.casefold().split() == new_value.casefold().split()

    def missing(*names: str) -> str:
        """The papers missing any of these metadata, e.g. 'a.xml and b.xml'"""
        return ' and '.join(
            doc.file_name
            for doc in (old_doc, new_doc)
            if any(name in doc.missing_meta for name in names)
        )

    def stage(doc: SupDocument) -> str:
        return f'{doc.meta_stage} ({doc.meta_house})'

    warnings: list[PaperWarning] = []

    if papers := missing('House', 'Stage'):
        warnings.append(
            PaperWarning(
                'Could not check that these papers are from the same stage.',
                f'The house or stage is missing from the metadata in {papers}.',
            )
        )
    elif not (
        same(old_doc.meta_house, new_doc.meta_house)
        and same(old_doc.meta_stage, new_doc.meta_stage)
    ):
        warnings.append(
            PaperWarning(
                'These papers are from different stages.',
                f'{old_doc.file_name} is from the {stage(old_doc)} and'
                f' {new_doc.file_name} is from the {stage(new_doc)}. Amendment'
                ' numbers start again at each stage, so amendments with the same'
                ' number on the two papers are probably different amendments,'
                ' and this report will compare the wrong amendments.',
                papers_differ=True,
            )
        )

    if papers := missing('Bill Title'):
        warnings.append(
            PaperWarning(
                'Could not check that these papers are for the same bill.',
                f'The bill title is missing from the metadata in {papers}.',
            )
        )
    elif not same(old_doc.meta_bill_title, new_doc.meta_bill_title):
        warnings.append(
            PaperWarning(
                'These papers are for different bills.',
                f'{old_doc.file_name} is for the {old_doc.meta_bill_title} and'
                f' {new_doc.file_name} is for the {new_doc.meta_bill_title}.',
                papers_differ=True,
            )
        )

    return warnings


class AmdtPair(NamedTuple):
    """The same amendment (or what may be) on the older and newer paper"""

    old: Amendment
    new: Amendment


def check_numbers_and_dnums(
    old_doc: SupDocument, new_doc: SupDocument
) -> tuple[list[AmdtPair], list[AmdtPair]]:
    """
    Check, using dnums, that amendments matched by number are the same
    amendment. A dnum is LawMaker's own reference for an amendment, e.g.
    HoC72.

    Returns two lists, in newer-paper order:
    - Numbers on both papers with different dnums. These may be different
      amendments (unusual, but possible in either House), and the report
      would then compare the wrong ones.
    - Dnums on both papers with different numbers: an amendment that has
      been renumbered, which the report shows as removed and added.

    Amendments with no dnum are not checked. Only the first amendment with
    each number is used, as in the rest of the report.

    This report matches amendments by number only, following Commons
    conventions (numbers stay the same within a stage), and only uses dnums
    for this check. check_web_amdts.py is different: its AmdtRef matches on
    number and dnum together, because Lords running lists often have dnums
    only (numbers are added late).
    """

    same_num_different_dnum = [
        AmdtPair(old_doc[num], new_amdt)
        for num, new_amdt in new_doc.items()
        if num in old_doc
        and old_doc[num].dnum
        and new_amdt.dnum
        and old_doc[num].dnum != new_amdt.dnum
    ]

    old_by_dnum = {amdt.dnum: amdt for amdt in old_doc.values() if amdt.dnum}
    same_dnum_different_num = [
        AmdtPair(old_by_dnum[new_amdt.dnum], new_amdt)
        for new_amdt in new_doc.values()
        if new_amdt.dnum in old_by_dnum
        and old_by_dnum[new_amdt.dnum].num != new_amdt.num
    ]

    return same_num_different_dnum, same_dnum_different_num


def order_items(doc: SupDocument) -> list[Item]:
    """
    The paper's amendment numbers and headings, in paper order, for
    marshalling.align.

    Commons only for now: amendments are matched by number, as in the rest
    of this report, because Commons amendment numbers stay the same within a
    stage. Lords running lists usually have dnums only (numbers are added
    late), so Lords papers would need matching on dnum.

    If several amendments share a number, only the first is used, as in the
    rest of the report (see SupDocument.duplicate_nums).
    """

    return [
        item if isinstance(item, Heading) else item.num
        for item in doc.sequence
        if isinstance(item, Heading) or doc[item.num] is item
    ]


# --------- Phrases for the Moved amendments card (plain text) ---------- #


def join_nums(nums: Sequence[str]) -> str:
    """e.g. '1', '1 and 2', or '1, 2 and 3'"""

    if len(nums) <= 1:
        return ''.join(nums)
    return f'{", ".join(nums[:-1])} and {nums[-1]}'


def describe_place(after: str | None, before: str | None) -> str:
    """
    Where amendments are, from the nearest unmoved amendments either side,
    e.g. 'between 2 and 3'. None means there is no unmoved amendment on that
    side (the amendments are at the start or end of the paper).
    """

    if after and before:
        return f'between {after} and {before}'
    if after:
        return f'after {after}'
    if before:
        return f'before {before}'
    # marshalling.align always leaves at least one amendment unmoved, so
    # there is always one on at least one side
    raise ValueError('There is no unmoved amendment on either side')


def first_heading(under: tuple[Heading, ...]) -> str:
    """
    The first heading in a block of headings, e.g. 'SECOND DAY' from SECOND
    DAY followed by NEW CLAUSES AND NEW SCHEDULES RELATING TO... The others
    are long, and the full headings are in the side-by-side view. Returns ''
    when there are no headings.
    """

    return under[0].text if under else ''


class Report:
    """
    Container for Amendment Report.
    The report summarises changes changes between two LM XML official list documents.
    Both papers should be from the same stage of the same bill (see
    check_papers_match).
    There are assumed to be no published documents between the two documents,
    if there are then the star check will be inaccurate
    """

    def __init__(
        self,
        old_file: Path | _Element,
        new_file: Path | _Element,
        days_between_papers: bool = False,
    ):
        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f'Error parsing HTML template file: {e}')
            raise

        self.days_between_papers = days_between_papers

        self.old_doc = SupDocument(old_file)
        self.new_doc = SupDocument(new_file)

        # e.g. the papers are from different stages. Shown at the top of the
        # report, but the report is still made.
        self.paper_warnings = check_papers_match(self.old_doc, self.new_doc)
        for warning in self.paper_warnings:
            logger.warning(f'{warning.summary} [{warning.detail}]')

        self.removed_amdts: list[str] = []
        self.added_amdts: list[str] = []

        self.no_name_changes: list[str] = []
        self.name_changes: list[ChangedNames] = []
        self.duplicate_names: list[str] = []
        self.name_changes_in_context: list[ChangedAmdt] = []

        self.correct_stars: list[str] = []
        self.incorrect_stars: list[str] = []

        self.changed_amdts: list[ChangedAmdt] = []

        # How the order of the amendments changed (see marshalling.py). None
        # when the papers are from different stages or bills.
        self.order: Alignment | None = None

        # Amendments whose numbers and dnums don't agree between the papers
        # (see check_numbers_and_dnums). Not checked when the papers are from
        # different stages or bills.
        self.same_num_different_dnum: list[AmdtPair] = []
        self.same_dnum_different_num: list[AmdtPair] = []

        # populate above lists of changes
        self.gather_changes()
        # build up the html document
        self.make_html()  # this does not save the html document

    def gather_changes(self):
        """
        Loop thorugh all amendments in the new document and compare them
        against the same amendment in the old document (if possible),
        populate the various lists of changes
        """

        self.added_and_removed_amdts(self.old_doc, self.new_doc)

        # On papers from different stages or bills, the same number is
        # usually a different amendment, so there is no point comparing the
        # order or checking dnums. The paper warnings card already says so.
        if not any(warning.papers_differ for warning in self.paper_warnings):
            self.order = align(order_items(self.old_doc), order_items(self.new_doc))
            self.same_num_different_dnum, self.same_dnum_different_num = (
                check_numbers_and_dnums(self.old_doc, self.new_doc)
            )

        if self.same_num_different_dnum:
            nums = ', '.join(pair.new.num for pair in self.same_num_different_dnum)
            logger.warning(
                'Some amendment numbers are on both papers with different dnums,'
                f' so they may be different amendments. [{nums}]'
            )
        if self.same_dnum_different_num:
            dnums = ', '.join(pair.new.dnum for pair in self.same_dnum_different_num)
            logger.warning(
                'Some amendments have the same dnum but a different number on'
                f' each paper. [{dnums}]'
            )

        # for each amendment in the document
        # populate the star check, name changes and changes to existing amendments
        for key, new_amdt in self.new_doc.items():
            if key not in self.old_doc:
                # star should be black if this amendment is new.
                self.star_check(new_amdt, None)
                continue

            old_amend = self.old_doc[key]

            # star should either be white or not exist if this amendment is not new
            self.star_check(new_amdt, old_amend)
            self.diff_names(new_amdt, old_amend)
            self.diff_names_in_context(new_amdt, old_amend)
            self.diff_amdt_content(new_amdt, old_amend)

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
                self.render_paper_warnings(),
                self.render_duplicate_amdt_nums(),
                self.render_numbers_and_dnums(),
                self.render_added_and_removed_amdts(),
                self.render_moved_amdts(),
                self.render_added_and_removed_names(),
                self.render_stars(),
                self.render_changed_amdts(),
            )
        )

    def render_intro(self) -> HtmlElement:
        # ------------------------- intro section ------------------------ #
        into = (
            'This report summarises changes between two LawMaker'
            ' XML official list documents. The documents are:'
            f'<br><strong>{self.old_doc.file_name}</strong> and '
            f'<strong>{self.new_doc.file_name}</strong>'
        )

        meta_data_table = templates.Table(
            ('', self.old_doc.file_name, self.new_doc.file_name)
        )

        meta_data_table.add_row(
            ('File path', self.old_doc.file_path, self.new_doc.file_path)
        )
        meta_data_table.add_row(
            ('Bill Title', self.old_doc.meta_bill_title, self.new_doc.meta_bill_title)
        )
        meta_data_table.add_row(
            ('House', self.old_doc.meta_house, self.new_doc.meta_house)
        )
        meta_data_table.add_row(
            ('Stage', self.old_doc.meta_stage, self.new_doc.meta_stage)
        )
        meta_data_table.add_row(
            ('Published date', self.old_doc.meta_pub_date, self.new_doc.meta_pub_date)
        )
        meta_data_table.add_row(
            ('List Type', self.old_doc.meta_list_type, self.new_doc.meta_list_type)
        )

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

    def render_paper_warnings(self) -> HtmlElement:
        """
        Warn that the papers may not be comparable, e.g. because they are
        from different stages. This affects every check in the report, so
        the card goes straight after the intro.
        """

        if not self.paper_warnings:
            # nothing to show so just return an empty div
            return html.Element('div')

        content = ''.join(
            f'<p><strong class="red">{escape(warning.summary)}</strong>'
            f' {escape(warning.detail)}</p>'
            for warning in self.paper_warnings
        )

        card = templates.Card('Are these the right papers?')
        card.secondary_info.extend(
            html.fragments_fromstring(content, no_leading_text=True)
        )

        return card.html

    def render_duplicate_amdt_nums(self) -> HtmlElement:
        """
        Warn about amendment numbers used more than once in either paper.

        Amendments are matched by number, so only the first amendment with a
        given number is compared. The others are left out of every check
        below, which is why this card goes near the top of the report.
        """

        docs_with_duplicates = [
            doc for doc in (self.old_doc, self.new_doc) if doc.duplicate_nums
        ]

        if not docs_with_duplicates:
            # nothing to show so just return an empty div
            return html.Element('div')

        def describe(amdt: Amendment) -> str:
            dnum = amdt.dnum or 'no dnum'
            proposer = amdt.names[0] if amdt.names else 'no proposer'
            return f'{escape(dnum)}, {escape(proposer)}'

        content = (
            '<p>Amendment numbers should be unique. <span class="red">The'
            ' numbers below are used more than once.</span> Only the first'
            ' amendment with each number has been compared, so the others are'
            ' not included in any of the checks in this report.</p>'
        )

        for doc in docs_with_duplicates:
            content += f'<p><strong>{escape(doc.file_name)}</strong></p><ul>'
            for num, amdts in doc.duplicate_nums.items():
                described = '; '.join(describe(amdt) for amdt in amdts)
                content += (
                    f'<li>{escape(num)}: {len(amdts)} amendments ({described})</li>'
                )
            content += '</ul>'

        card = templates.Card('Duplicate amendment numbers')
        card.secondary_info.extend(
            html.fragments_fromstring(content, no_leading_text=True)
        )

        return card.html

    def render_numbers_and_dnums(self) -> HtmlElement:
        """
        Warn about amendments whose numbers and dnums don't agree between
        the papers (see check_numbers_and_dnums). Like duplicate numbers,
        this affects every check in the report, so the card goes near the top.
        """

        if not (self.same_num_different_dnum or self.same_dnum_different_num):
            # nothing to show so just return an empty div
            return html.Element('div')

        content = ''

        if self.same_num_different_dnum:
            content += (
                '<p>These numbers are on both papers with different dnums, so'
                ' they may be different amendments. This report compares'
                ' amendments by number, so check them by hand.</p><ul>'
            )
            for old, new in self.same_num_different_dnum:
                content += (
                    f'<li>{escape(new.num)}: {escape(old.dnum)} on the older'
                    f' paper, {escape(new.dnum)} on the newer</li>'
                )
            content += '</ul>'

        if self.same_dnum_different_num:
            content += (
                '<p>These amendments have the same dnum but a different number'
                ' on each paper, so this report shows each one as removed and'
                ' added.</p><ul>'
            )
            for old, new in self.same_dnum_different_num:
                content += (
                    f'<li>{escape(new.dnum)}: {escape(old.num)} on the older'
                    f' paper, {escape(new.num)} on the newer</li>'
                )
            content += '</ul>'

        card = templates.Card('Amendment numbers and dnums')
        card.secondary_info.extend(
            html.fragments_fromstring(content, no_leading_text=True)
        )

        return card.html

    def render_added_and_removed_amdts(self) -> HtmlElement:
        # ----------- Removed and added amendments section ----------- #
        # build up text content
        removed_content = 'Removed content: <strong>None</strong>'
        if self.removed_amdts:
            removed_content = (
                f'Removed content: <strong>{len(self.removed_amdts)}</strong><br />'
                f'{" ".join(self.removed_amdts)}'
            )
        added_content = 'Added content: <strong>None</strong>'
        if self.added_amdts:
            added_content = (
                f'Added content: <strong>{len(self.added_amdts)}</strong><br />'
                f'{" ".join(self.added_amdts)}'
            )

        card = templates.Card('Added and removed amendments')
        card.secondary_info.extend(
            [
                html.fromstring(f'<p>{added_content}</p>'),
                html.fromstring(f'<p>{removed_content}</p>'),
            ]
        )
        return card.html

    def render_moved_amdts(self) -> HtmlElement:
        """
        Summarise how the order of the amendments changed (see
        marshalling.py): which amendments moved, where they are now and
        where they were. The moves are grouped by where they are now. Added
        and removed amendments are listed too, in paper order.
        """

        card = templates.Card('Moved amendments')

        if self.order is None:
            content = (
                '<p>Not checked, because these papers are from different stages'
                ' or for different bills (see above).</p>'
            )
        else:
            content = self.moved_amdts_html(self.order)

        card.secondary_info.extend(
            html.fragments_fromstring(content, no_leading_text=True)
        )

        return card.html

    def moved_amdts_html(self, order: Alignment) -> str:
        """The content of the Moved amendments card"""

        on_both = len(order.unmoved) + len(order.moved)
        moved = len(order.moved)

        if on_both == 0:
            content = '<p>No amendments are on both papers.</p>'
        elif moved == 0:
            content = '<p>No amendments have moved.'
            if on_both > 1:
                content += (
                    f' The {on_both} amendments on both papers are in the same order.'
                )
            content += '</p>'
        else:
            content = (
                '<p>These amendments are in a different place, compared with the'
                ' amendments around them, from where they were on the older'
                ' paper. As few amendments as possible are counted as moved, so'
                ' when a block of amendments moves, the block is listed, not'
                ' everything around it. “Between” refers to amendments that'
                ' have not moved.</p>'
                f'<p>Of the {on_both} amendments on both papers, {moved}'
                f' {"has" if moved == 1 else "have"} moved.</p>'
                '<ul>'
            )

            for group in order.groups:
                count = len(group.keys)
                now_heading = first_heading(group.now_under)

                # e.g. '2 amendments are now between NC83 and NC88, under
                # SECOND DAY'
                content += (
                    f'<li><strong>{count} amendment{"" if count == 1 else "s"}'
                    f'</strong> {"is" if count == 1 else "are"} now'
                    f' {escape(describe_place(group.now_after, group.now_before))}'
                )
                if now_heading:
                    content += f', under {escape(now_heading)}'
                content += '<ul>'

                for run in group.runs:
                    # e.g. 'NC86 and NC87 were between NC85 and NC90, under
                    # FIRST DAY'. The heading is only given if it is different.
                    was_heading = first_heading(run.was_under)
                    content += (
                        f'<li>{escape(join_nums(run.keys))}'
                        f' {"was" if len(run.keys) == 1 else "were"}'
                        f' {escape(describe_place(run.was_after, run.was_before))}'
                    )
                    if was_heading and was_heading != now_heading:
                        content += f', under {escape(was_heading)}'
                    content += '</li>'

                content += '</ul></li>'

            content += '</ul>'

        # the same amendments as the Added and removed amendments card, but in
        # paper order and folded away
        for label, nums in (
            ('Added amendments', order.added),
            ('Removed amendments', order.removed),
        ):
            if nums:
                content += (
                    f'<details><summary>{label} ({len(nums)})</summary>'
                    f'<p>{escape(" ".join(nums))}</p></details>'
                )

        return content

    def added_and_removed_names_table(self) -> HtmlElement:
        if not self.name_changes:
            return html.fromstring(
                '<p><strong>Zero</strong> amendments have name changes.</p>'
            )

        name_changes = templates.Table(
            ('Ref', 'Names added', 'Names removed', 'Totals')
        )

        # we have a special class for this table
        name_changes.html.classes.add('an-table')  # type: ignore

        for item in self.name_changes:
            names_added = []
            for name in item.added:
                names_added.append(
                    html.fromstring(
                        f'<span class="col-12 col-lg-6  mb-2">{name}</span>'
                    )
                )
            p_names_added = html.fromstring('<p class="row"></p>')
            p_names_added.extend(names_added)

            total_added = len(item.added)
            total_removed = len(item.removed)
            totals = []
            if total_added:
                totals.append(f'Added: {total_added}')
            if total_removed:
                totals.append(f'Removed: {total_removed}')

            name_changes.add_row(
                (item.num, p_names_added, ', '.join(item.removed), ', '.join(totals))
            )

        return name_changes.html

    def render_added_and_removed_names(self) -> HtmlElement:
        """Added and removed names section"""

        no_name_changes = html.fromstring(
            '<p><strong>Zero</strong> amendments have no name changes.</p>'
        )

        if self.no_name_changes:
            sec = templates.SmallCollapsableSection(
                f'<span><strong>{len(self.no_name_changes)}</strong>'
                f' amendments have no name changes: '
                '<small class="text-muted"> [show]</small></span>'
            )
            sec.collapsible.text = f'{", ".join(self.no_name_changes)}'
            no_name_changes = sec.html

        name_changes_table = self.added_and_removed_names_table()

        # Name changes in context
        names_change_context_section = templates.NameChangeContextSection()

        # build up text content
        changed_amdts = []
        if self.name_changes_in_context:
            changed_amdts.append(
                html.fromstring(
                    f'<p><strong>{len(self.name_changes_in_context)}</strong>'
                    ' amendments have changed names: </p>\n'
                )
            )
            for item in self.name_changes_in_context:
                changed_amdts.append(
                    html.fromstring(
                        "<div><p class='h5"
                        f" mt-4'>{item.num}:</p>\n{item.html_diff}\n</div>"
                    )
                )
        else:
            logger.info('No name changes in context')

        names_change_context_section.add_content(changed_amdts)

        if len(self.name_changes_in_context) == 0:
            # might as well not output anything if not necessary
            names_change_context_section.clear()

        card = templates.Card('Added and removed names')
        card.secondary_info.extend(
            (
                name_changes_table,
                names_change_context_section.html,
            )
        )
        card.tertiary_info.append(no_name_changes)

        return card.html

    def render_stars(self) -> HtmlElement:
        # -------------------- Star check section -------------------- #
        # build up text content
        correct_stars = html.fromstring(
            '<p><strong>Zero</strong> amendments have correct stars.</p>'
        )
        if self.correct_stars:
            sec = templates.SmallCollapsableSection(
                f'<span><strong>{len(self.correct_stars)}</strong>'
                f' amendments have correct stars: '
                '<small class="text-muted"> [show]</small></span>'
            )
            sec.collapsible.text = f'{", ".join(self.correct_stars)}'
            correct_stars = sec.html

        incorrect_stars = '<strong>Zero</strong> amendments have incorrect stars'
        if self.incorrect_stars:
            incorrect_stars = (
                f'<strong class="red">{len(self.incorrect_stars)} amendments'
                f' have incorrect stars:</strong>  {", ".join(self.incorrect_stars)}'
            )

        card = templates.Card('Star Check')
        card.secondary_info.append(html.fromstring(f'<p>{incorrect_stars}</p>'))
        card.tertiary_info.append(correct_stars)
        # self.add_element_to_output_html(card.html)
        return card.html

    def render_changed_amdts(self) -> HtmlElement:
        # -------------------- Changed Amendments -------------------- #
        # build up text content
        changed_amdts = '<p><strong>Zero</strong> amendments have changed content.</p>'
        if self.changed_amdts:
            changed_amdts = (
                f'<p><strong class="red">{len(self.changed_amdts)}</strong>'
                ' amendments have changed content: </p>\n'
            )
            for item in self.changed_amdts:
                changed_amdts += f"<p class='h5'>{item.num}:</p>\n{item.html_diff}\n"

        card = templates.Card('Changed amendments')
        card.secondary_info.extend(
            html.fragments_fromstring(changed_amdts, no_leading_text=True)
        )

        return card.html

    def star_check(
        self,
        new_amdt: Amendment,
        old_amdt: Amendment | None,
    ):
        """
        New amendments should have a black star.

        if there are no sitting or printing days between the two documents:
        * Amendments which previously had a black star should now have a white star.
        * Amendments which previously had a white star should now have no star.

        If there are sitting or printing days between the two documents:
        * Amendments which previously a star of any colour should now have no star.

        In either case:
        * Amendments which previously had no star should still have no star.
        """

        if old_amdt is None:
            if new_amdt.star == BLACK_STAR:
                self.correct_stars.append(f'{new_amdt.num} ({new_amdt.star})')
            else:
                self.incorrect_stars.append(
                    f'{new_amdt.num} has {new_amdt.star} ({BLACK_STAR} expected)'
                )

        elif old_amdt.star in (BLACK_STAR, WHITE_STAR):
            expected_star = old_amdt.star.next_star(self.days_between_papers)
            if new_amdt.star == expected_star:
                self.correct_stars.append(f'{new_amdt.num} ({new_amdt.star})')
            else:
                self.incorrect_stars.append(
                    f'{new_amdt.num} has {new_amdt.star} ({expected_star} expected)'
                )

        elif old_amdt.star == NO_STAR:
            # A standing amendment with no star should never get a star back.
            # Only report it when it is wrong. Adding every correct no-star
            # amendment to correct_stars would swamp that list (e.g. 228 in
            # the Energy example), which is meant to show stars that changed.
            if new_amdt.star != NO_STAR:
                self.incorrect_stars.append(
                    f'{new_amdt.num} has {new_amdt.star} ({NO_STAR} expected)'
                )

        else:
            # there is an error with the star in the input XML
            self.incorrect_stars.append(
                f'Error with star in {old_amdt.parent_doc.file_name},'
                f' {old_amdt.num} check manually.'
            )

    def added_and_removed_amdts(self, old_doc: 'SupDocument', new_doc: 'SupDocument'):
        """Find the amendment numbers which have been added and removed"""

        self.removed_amdts = list(old_doc.amdt_set.difference(new_doc.amdt_set))
        self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

        # return removed_amdts, added_amdts

    def diff_names(self, new_amdt: Amendment, old_amdt: Amendment):
        # look for duplicate names. Only need to do this for the new_amdt.
        self.duplicate_names = find_duplicates(new_amdt.names)

        if self.duplicate_names:
            # warn in UI
            logger.warning(f'Duplicate names found in {new_amdt.num}')

        added_names = [item for item in new_amdt.names if item not in old_amdt.names]
        removed_names = [item for item in old_amdt.names if item not in new_amdt.names]

        if not added_names and not removed_names:
            # there have been no name changes
            self.no_name_changes.append(new_amdt.num)
        else:
            self.name_changes.append(
                ChangedNames(new_amdt.num, added_names, removed_names)
            )

    def diff_names_in_context(self, new_amdt: Amendment, old_amdt: Amendment):
        """
        Create an HTML string containing a tables showing the differences
        between old_amdt//amendmentHeading and new_amdt//amendmentHeading.

        amendmentHeading is the element which contains the sponsors.
        It does not contain the amendment body.
        """

        new_amdt_heading = xp.get_amdt_heading(new_amdt.xml)
        old_amdt_heading = xp.get_amdt_heading(old_amdt.xml)

        try:
            # make sure heading elements found
            new_amdt_heading = new_amdt_heading[0]
            old_amdt_heading = old_amdt_heading[0]

            # and make sure children
            assert len(new_amdt_heading) > 0
            assert len(old_amdt_heading) > 0

        except (IndexError, AssertionError):
            logger.warning(f'{new_amdt.num}: no sponsors found')
            return

        dif_html_str = diff_xml_content(
            new_amdt_heading,
            old_amdt_heading,
            fromdesc=old_amdt.parent_doc.file_name,
            todesc=new_amdt.parent_doc.file_name,
        )
        if dif_html_str is not None:
            self.name_changes_in_context.append(ChangedAmdt(new_amdt.num, dif_html_str))

    def diff_amdt_content(self, new_amdt: Amendment, old_amdt: Amendment):
        """
        Create an HTML string containing a tables showing the differences
        between old_amdt//amendmentContent and new_amdt//amendmentContent.

        amendmentContent is the element which contains the text of the
        amendment. It does not contain the sponsor information.
        """

        new_amdt_content = xp.get_amdt_content(new_amdt.xml)
        old_amdt_content = xp.get_amdt_content(old_amdt.xml)

        if len(new_amdt_content) == 0 or len(old_amdt_content) == 0:
            logger.warning(f'{new_amdt.num}: has no content')
            return
        else:
            new_amdt_content = new_amdt_content[0]
            old_amdt_content = old_amdt_content[0]

        dif_html_str = diff_xml_content(
            new_amdt_content,
            old_amdt_content,
            fromdesc=old_amdt.parent_doc.file_name,
            todesc=new_amdt.parent_doc.file_name,
        )
        if dif_html_str is not None:
            self.changed_amdts.append(ChangedAmdt(new_amdt.num, dif_html_str))


def main():
    lawchecker_logger.setup_lawchecker_logging()
    parser = argparse.ArgumentParser(
        description=(
            'Create an HTML document with various automated checks on amendments.'
            ' Both papers should be from the same stage of the same bill.'
        )
    )

    parser.add_argument(
        'old_doc',
        type=Path,
        help='The amendment paper from a previous day',
    )

    parser.add_argument(
        'new_doc',
        type=Path,
        help='The amendment paper you wish to check',
    )

    parser.add_argument(
        '-d',
        '--days-between',
        action='store_true',
        help='Use this flag if there are sitting days between the documents compared',
    )

    args = parser.parse_args(sys.argv[1:])

    filename = 'html_diff.html'

    report = Report(args.old_doc, args.new_doc, days_between_papers=args.days_between)

    report.html_tree.write(
        filename,
        method='html',
        encoding='utf-8',
        doctype='<!DOCTYPE html>',
    )

    webbrowser.open(Path(filename).resolve().as_uri())


if __name__ == '__main__':
    main()
