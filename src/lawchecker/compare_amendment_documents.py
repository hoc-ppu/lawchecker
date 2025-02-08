#!/usr/bin/env python3

import argparse
import sys
import webbrowser
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from lxml import etree, html
from lxml.etree import QName, _Element

from lawchecker import templates
from lawchecker import xpath_helpers as xp
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, NSMAP2, UKL
from lawchecker.stars import BLACK_STAR, NO_STAR, WHITE_STAR, Star
from lawchecker.utils import diff_xml_content, truncate_string

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
# [x] warn if old XML file and new XML file seem to be the wrong way around,
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


class Amendment:
    def __init__(self, amdt: _Element, parent_doc: "SupDocument"):
        self.parent_doc = parent_doc
        _num = amdt.find(
            "amendment/amendmentBody/amendmentContent/tblock/num", namespaces=NSMAP2
        )
        _xml = amdt.find("amendment/amendmentBody", namespaces=NSMAP2)
        self._names: list[str] | None = None
        self.star = Star(amdt.get(QName(UKL, "statusIndicator"), default=""))

        if _num is not None and _num.text and _xml is not None:
            self.num: str = _num.text
            self.xml: _Element = _xml
        else:
            logger.warning(f"{_num=}, {_xml=}")
            raise ValueError(
                "amendmentBody or amendmentBody/amendmentContent/tblock/num is None"
            )

    @property
    def names(self) -> list[str]:
        """
        List of the names of the MPs who proposed and supported the amendment
        """

        if self._names is None:
            self._names = [
                name_element.text
                for name_element in xp.get_name_elements(self.xml)
                if name_element.text
            ]

        return self._names


class SupDocument(Mapping):
    """Container for an amendment document aka official list"""

    def __init__(self, xml: Path | _Element):
        if isinstance(xml, Path):
            self.file_name = xml.name
            self.file_path = str(xml.resolve())
            tree = etree.parse(self.file_path)
            self.root = tree.getroot()
        else:
            self.file_name = "Test"
            self.file_path = "test/Test"
            tree = etree.ElementTree(xml)
            self.root = xml

        self.short_file_name = truncate_string(self.file_name).replace(".xml", "")

        # build up metadata
        self.meta_list_type: str
        self.meta_bill_title: str
        self.meta_pub_date: str

        self.get_meta_data()

        self.problem_amendments = 0
        self.amendments: list[Amendment] = []

        for amdt_xml in xp.get_amendments(self.root):
            try:
                amendment = Amendment(amdt_xml, self)
                self.amendments.append(amendment)
            except ValueError as e:
                logger.warning(repr(e))
                self.problem_amendments += 1

        self._dict = self._create_amdt_map()
        self.amdt_set = set(self._dict.keys())

    def get_meta_data(self):
        try:
            list_type = self.root.find(".//block[@name='listType']", namespaces=NSMAP2)
            self.meta_list_type = list_type.text  # type: ignore
        except Exception as e:
            warning_msg = f"Can't find List Type meta data. Check {self.file_name}"
            self.meta_list_type = warning_msg
            logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

        try:
            bill_title = self.root.find(
                ".//TLCConcept[@eId='varBillTitle']", namespaces=NSMAP2
            )
            # don't use .get here  as that defaults to None
            self.meta_bill_title = bill_title.attrib["showAs"]  # type: ignore
            # [x] test
        except Exception as e:
            warning_msg = f"Can't find Bill Title meta data. Check {self.file_name}"
            self.meta_bill_title = warning_msg
            logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

        try:
            # add a test for this
            published_date = self.root.find(
                ".//FRBRManifestation/FRBRdate[@name='published']", namespaces=NSMAP2
            )
            self.meta_pub_date = datetime.strptime(
                published_date.get("date", default=""), "%Y-%m-%d"  # type: ignore
            ).strftime("%A %d %B %Y")

        except Exception as e:
            warning_msg = f"Can't find Published Date meta data. Check {self.file_name}"
            self.meta_pub_date = warning_msg
            if not isinstance(e, AttributeError):
                warning_msg += f": {repr(e)}"
            logger.info(f"Problem parsing XML. {warning_msg}")

    def _create_amdt_map(self) -> dict[str, Amendment]:
        _amdt_map: dict[str, Amendment] = {}

        for amendment in self.amendments:
            if amendment.num in _amdt_map:
                logger.warning(f"Duplicate amendment number: {amendment.num}")
            _amdt_map[amendment.num] = amendment

        return _amdt_map

    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __contains__(self, key):
        return key in self._dict

    def items(self):
        return self._dict.items()



class Report:

    """
    Container for Amendment Report.
    The report summarises changes changes between two LM XML official list documents.
    There are assumed to be no published documents between the two documents,
    if there are then the star check will be inaccurate
    """

    def __init__(
        self,
        old_file: Path | _Element,
        new_file: Path | _Element,
        days_between_papers: bool = False
    ):
        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f"Error parsing HTML template file: {e}")
            raise

        self.days_between_papers = days_between_papers

        self.old_doc = SupDocument(old_file)
        self.new_doc = SupDocument(new_file)

        self.removed_amdts: list[str] = []
        self.added_amdts: list[str] = []

        self.no_name_changes: list[str] = []
        self.name_changes: list[ChangedNames] = []
        self.duplicate_names: list[str] = []
        self.name_changes_in_context: list[ChangedAmdt] = []

        self.correct_stars: list[str] = []
        self.incorrect_stars: list[str] = []

        self.changed_amdts: list[ChangedAmdt] = []

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

        # for each amendment in the document
        # populate the star check, name changes and changes to existing amendments
        for key, new_amdt in self.new_doc.items():
            if key not in self.old_doc:
                # the star check only happens when there is no coresponding
                # amendment in previous document
                self.star_check(new_amdt, None)
                continue

            old_amend = self.old_doc[key]

            self.star_check(new_amdt, old_amend)
            self.diff_names(new_amdt, old_amend)
            self.diff_names_in_context(new_amdt, old_amend)
            self.diff_amdt_content(new_amdt, old_amend)

    def make_html(self):
        """
        Build up HTML document with various automated checks on amendments
        """
        xp = './/div[@id="content-goes-here"]'
        insert_point: _Element = self.html_root.find(xp)  # type: ignore
        # print(etr)
        insert_point.extend(
            (
                self.render_intro(),
                self.render_added_and_removed_amdts(),
                self.render_added_and_removed_names(),
                self.render_stars(),
                self.render_changed_amdts(),
            )
        )

    def render_intro(self) -> _Element:
        # ------------------------- intro section ------------------------ #
        into = (
            "This report summarises changes between two LawMaker"
            " XML official list documents. The documents are:"
            f"<br><strong>{self.old_doc.file_name}</strong> and "
            f"<strong>{self.new_doc.file_name}</strong>"
        )

        meta_data_table = templates.Table(
            ("", self.old_doc.file_name, self.new_doc.file_name)
        )

        meta_data_table.add_row(
            ("File path", self.old_doc.file_path, self.new_doc.file_path)
        )
        meta_data_table.add_row(
            ("Bill Title", self.old_doc.meta_bill_title, self.new_doc.meta_bill_title)
        )
        meta_data_table.add_row(
            ("Published date", self.old_doc.meta_pub_date, self.new_doc.meta_pub_date)
        )
        meta_data_table.add_row(
            ("List Type", self.old_doc.meta_list_type, self.new_doc.meta_list_type)
        )

        section = html.fromstring(
            '<div class="wrap">'
            '<section id="intro">'
            "<h2>Introduction</h2>"
            f"<p>{into}</p>"
            "</section>"
            "</div>"
        )

        section.append(meta_data_table.html)

        return section

    def render_added_and_removed_amdts(self) -> _Element:
        # ----------- Removed and added amendments section ----------- #
        # build up text content
        removed_content = "Removed content: <strong>None</strong>"
        if self.removed_amdts:
            removed_content = (
                f"Removed content: <strong>{len(self.removed_amdts)}</strong><br />"
                f"{' '.join(self.removed_amdts)}"
            )
        added_content = "Added content: <strong>None</strong>"
        if self.added_amdts:
            added_content = (
                f"Added content: <strong>{len(self.added_amdts)}</strong><br />"
                f"{' '.join(self.added_amdts)}"
            )

        card = templates.Card("Added and removed amendments")
        card.secondary_info.extend([
            html.fromstring(f"<p>{added_content}</p>"),
            html.fromstring(f"<p>{removed_content}</p>")
        ])
        return card.html

    def added_and_removed_names_table(self) -> _Element:

        if not self.name_changes:
            return html.fromstring(
                "<p><strong>Zero</strong> amendments have name changes.</p>"
            )

        name_changes = templates.Table(("Ref", "Names added", "Names removed", "Totals"))

        # we have a special class for this table
        name_changes.html.classes.add("an-table")  # type: ignore

        for item in self.name_changes:
            names_added = []
            for name in item.added:
                names_added.append(
                    html.fromstring(
                        f'<span class="col-12 col-lg-6  mb-2">{name}</span>'
                    )
                )
            p_names_added = etree.fromstring('<p class="row"></p>')
            p_names_added.extend(names_added)

            total_added = len(item.added)
            total_removed = len(item.removed)
            totals = []
            if total_added:
                totals.append(f"Added: {total_added}")
            if total_removed:
                totals.append(f"Removed: {total_removed}")

            name_changes.add_row(
                (item.num, p_names_added, ", ".join(item.removed), ", ".join(totals))
            )

        return name_changes.html

    def render_added_and_removed_names(self) -> _Element:

        """Added and removed names section"""

        no_name_changes = html.fromstring(
            "<p><strong>Zero</strong> amendments have no name changes.</p>"
        )

        if self.no_name_changes:

            sec = (templates.SmallCollapsableSection(
                f"<span><strong>{len(self.no_name_changes)}</strong>"
                f" amendments have no name changes: "
                '<small class="text-muted"> [show]</small></span>'
            ))
            sec.collapsible.text = f"{', '.join(self.no_name_changes)}"
            no_name_changes = sec.html

        name_changes_table = self.added_and_removed_names_table()

        # Name changes in context
        names_change_context_section = templates.NameChangeContextSection()

        # build up text content
        changed_amdts = []
        if self.name_changes_in_context:
            changed_amdts.append(
                html.fromstring(
                    f"<p><strong>{len(self.name_changes_in_context)}</strong> amendments"
                    " have changed names: </p>\n"
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
            logger.info("No name changes in context")

        names_change_context_section.add_content(changed_amdts)

        if len(self.name_changes_in_context) == 0:
            # might as well not output anything if not necessary
            names_change_context_section.clear()

        card = templates.Card("Added and removed names")
        card.secondary_info.extend(
            (
                name_changes_table,
                names_change_context_section.html,
            )
        )
        card.tertiary_info.append(no_name_changes)

        return card.html


    def render_stars(self) -> _Element:
        # -------------------- Star check section -------------------- #
        # build up text content
        correct_stars = html.fromstring(
            "<p><strong>Zero</strong> amendments have correct stars.</p>"
        )
        if self.correct_stars:

            sec = (templates.SmallCollapsableSection(
                f"<span><strong>{len(self.correct_stars)}</strong>"
                f" amendments have correct stars: "
                '<small class="text-muted"> [show]</small></span>'
            ))
            sec.collapsible.text = f"{', '.join(self.correct_stars)}"
            correct_stars = sec.html

        incorrect_stars = (
            "<strong>Zero</strong> amendments have incorrect stars"
        )
        if self.incorrect_stars:
            incorrect_stars = (
                f'<strong class="red">{len(self.incorrect_stars)} amendments'
                f" have incorrect stars:</strong>  {', '.join(self.incorrect_stars)}"
            )

        card = templates.Card("Star Check")
        card.secondary_info.append(html.fromstring(f"<p>{incorrect_stars}</p>"))
        card.tertiary_info.append(correct_stars)
        # self.add_element_to_output_html(card.html)
        return card.html

    def render_changed_amdts(self) -> _Element:
        # -------------------- Changed Amendments -------------------- #
        # build up text content
        changed_amdts = (
            "<p><strong>Zero</strong> amendments have changed content.</p>"
        )
        if self.changed_amdts:
            changed_amdts = (
                f'<p><strong class="red">{len(self.changed_amdts)}</strong>'
                " amendments have changed content: </p>\n"
            )
            for item in self.changed_amdts:
                changed_amdts += f"<p class='h5'>{item.num}:</p>\n{item.html_diff}\n"

        card = templates.Card("Changed amendments")
        card.secondary_info.extend(html.fragments_fromstring(changed_amdts))

        return card.html


    def star_check(
        self,
        new_amdt: Amendment,
        old_amdt: Amendment | None,
    ):

        """New amendments should have a black star.

        if there are no sitting or printing days between the two documents:
        * Amendments which previously had a black star should now have a white star.
        * Amendments which previously had a white star should now have no star.
        If there are sitting or printing days between the two documents:
        * Amendments which previously a star of any colour should now have no star."""

        if old_amdt is None:
            if new_amdt.star == BLACK_STAR:
                self.correct_stars.append(f"{new_amdt.num} ({new_amdt.star})")
            else:
                self.incorrect_stars.append(f"{new_amdt.num} has {new_amdt.star} ({BLACK_STAR} expected)")

        elif old_amdt.star in (BLACK_STAR, WHITE_STAR):

            expected_star = old_amdt.star.next_star(self.days_between_papers)
            if new_amdt.star == expected_star:
                self.correct_stars.append(f"{new_amdt.num} ({new_amdt.star})")
            else:
                self.incorrect_stars.append(f"{new_amdt.num} has {new_amdt.star} ({expected_star} expected)")

        elif old_amdt.star == NO_STAR:
            # do nothing
            pass

        else:
            # there is an error with the star in the input XML
            self.incorrect_stars.append(
                f"Error with star in {old_amdt.parent_doc.file_name},"
                f" {old_amdt.num} check manually."
            )


    def added_and_removed_amdts(self, old_doc: "SupDocument", new_doc: "SupDocument"):

        """Find the amendment numbers which have been added and removed"""

        self.removed_amdts = list(old_doc.amdt_set.difference(new_doc.amdt_set))
        self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

        # return removed_amdts, added_amdts

    def diff_names(self, new_amdt: Amendment, old_amdt: Amendment):
        # look for duplicate names. Only need to do this for the new_amdt.
        self.duplicate_names = find_duplicates(new_amdt.names)

        if self.duplicate_names:
            # warn in UI
            logger.warning(f"Duplicate names found in {new_amdt.num}")

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
            logger.warning(f"{new_amdt.num}: no sponsors found")
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
            logger.warning(f"{new_amdt.num}: has no content")
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

    parser = argparse.ArgumentParser(
        description=(
            "Create an HTML document with various automated checks on amendments."
        )
    )

    parser.add_argument(
        "old_doc",
        type=Path,
        help="The amendment paper from a previous day",
    )

    parser.add_argument(
        "new_doc",
        type=Path,
        help="The amendment paper you wish to check",
    )

    parser.add_argument(
        "-d",
        "--days-between",
        action="store_true",
        help="Use this flag if there are sitting days between the documents compared"
    )

    args = parser.parse_args(sys.argv[1:])

    filename = "html_diff.html"

    report = Report(
        args.old_doc,
        args.new_doc,
        days_between_papers=args.days_between
    )

    report.html_tree.write(
        filename,
        method="html",
        encoding="utf-8",
        doctype="<!DOCTYPE html>",
    )

    webbrowser.open(Path(filename).resolve().as_uri())


def find_duplicates(lst: list[str]) -> list[str]:

    # Convert the list to a set to remove duplicates
    unique_items = set(lst)

    # If the length of the set is less than the length of the list,
    # then there are duplicates
    if len(unique_items) < len(lst):

        sorted_items = sorted(list(unique_items))

        # Create a dictionary to store the count of each item
        item_counts = {}

        # Count the number of occurrences of each item in the original list
        for item in lst:
            if item in item_counts:
                item_counts[item] += 1
            else:
                item_counts[item] = 1

        # Create a list of duplicates
        return [item for item in sorted_items if item_counts[item] > 1]

    return list()



if __name__ == "__main__":
    main()
