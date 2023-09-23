#!/usr/bin/env python3

import argparse
import difflib
import re
import sys
import webbrowser
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, NamedTuple, Optional, TypeVar, cast

import templates
from logger import logger
from lxml import etree, html
from lxml.etree import QName, _Element
from lxml.html import builder as E

T = TypeVar("T")


# TODO: [x] put all sections in HTML document
# [x] add bootstrap to HTML
# Add messages for Nil return
# [x] say which documents are being compared
# [x] do the star check
# [x] read arguments from command line
# [x] make ANR respect omit-from-report setting
# [x] put logger in separate file
# warn about problem amendments in an error section
# [x] error if input file is not XML
# warn if no amendments found
# [x] open HTML file in browser
# [] pytest metadata
# Rearange total counts to be at the top
# [x] Put in added names GUI
# [x] change to pyside6 from pyQt5
# [x] shorten class Xpath
# put duplicate names back in output
# test on more example documents
# [x] put on GitHub
# [x] warn if bill titles don't match
# [x] warn if old XML file and new XML file seem to be the wrong way around,
#   i.e. if the old file seems newer than the new  file.

# think about changing 1 to A1 or Amendment 1... to make it look better in
# Added and removed amendments. See
# python3 check_amendments.py LM_XML/digital_rm_rep_0825.xml LM_XML/digital_rm_rep_0906.xml


HTML_TEMPLATE_FILE = "python/html_diff_template.html"

XMLNS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"  # akn is default ns
UKL = "https://www.legislation.gov.uk/namespaces/UK-AKN"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP: dict[str, str] = {"dns": XMLNS, "ukl": UKL, "xsi": XSI}

# empty prefix [i.e. key=""] is allowed in some lxml methods/functions but
# not others. E.g. it's allowed in find but not allowed in xpath
NSMAP2 = NSMAP.copy()
NSMAP2[""] = XMLNS


# ---------------------- create xpath functions ---------------------- #
class XPath(etree.XPath, Generic[T]):
    def __init__(
        self,
        path: str,
        expected_type: type[T],
        *,
        namespaces: Optional[Mapping[str, str]] = NSMAP,
        **kwargs: Any,
    ):
        super().__init__(
            path,
            namespaces=namespaces,
            **kwargs,
        )
        self.typ = expected_type

    def __call__(self, _etree_or_element, **_variables) -> T:
        typ = self.typ
        return cast(typ, super().__call__(_etree_or_element, **_variables))


get_amendments = XPath(
    "//dns:component[dns:amendment]",
    expected_type=list[_Element],
)

text_content = XPath("string()", expected_type=type(str()))

# get MP name elements. These are proposer and supporters elements
get_name_elements = XPath(
    (
        "dns:amendmentHeading/dns:block[@name='proposer' or"
        " @name='supporters']/*[@refersTo]"
    ),
    expected_type=list[_Element],
)

get_amdt_heading = XPath(
    "dns:amendmentHeading[1]",
    expected_type=list[_Element],
)

get_amdt_content = XPath(
    "dns:amendmentContent[1]",
    expected_type=list[_Element],
)


# html diff object
html_diff = difflib.HtmlDiff(tabsize=6)

nbsp = re.compile(r"(?<!&nbsp;)&nbsp;(?!</span>)(?!&nbsp;)")


class Amendment:
    def __init__(self, amdt: _Element, parent_doc: "SupDocument"):
        self.parent_doc = parent_doc
        _num = amdt.find(
            "amendment/amendmentBody/amendmentContent/tblock/num", namespaces=NSMAP2
        )
        _xml = amdt.find("amendment/amendmentBody", namespaces=NSMAP2)
        self._names: Optional[list[str]] = None
        self.star = amdt.get(f"{{{UKL}}}statusIndicator", None)

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
        """List of the names of the MPs who proposed and supported the amendment"""

        if self._names is None:
            self._names = [
                name_element.text
                for name_element in get_name_elements(self.xml)
                if name_element.text
            ]

        return self._names


class SupDocument(Mapping):
    """Container for an amendment document aka official list"""

    def __init__(self, file: Path):
        self.file_name = file.name
        self.file_path = str(file.resolve())
        tree = etree.parse(str(file))
        self.root = tree.getroot()

        # build up metadata
        self.meta_list_type: str
        self.meta_bill_title: str
        self.meta_pub_date: str

        self.get_meta_data()

        self.problem_amendments = 0
        self.amendments: list[Amendment] = []

        # for amdt in cast(list[_Element], self.root.xpath("//dns:amendment", namespaces=NSMAP)):
        for amdt_xml in get_amendments(self.root):
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
            logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

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


class ChangedNames(NamedTuple):
    num: str
    added: list[str]
    removed: list[str]


class ChangedAmdt(NamedTuple):
    num: str
    html_diff: str


class Report:

    """Container for Amendment Report.
    The report summarises changes changes between two LM XML official list documents.
    There are assumed to be no published documents between the two documents,
    if there are then the star check will be inaccurate"""

    def __init__(self, old_file: Path, new_file: Path):
        try:
            self.html_tree = html.parse(HTML_TEMPLATE_FILE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f"Error parsing HTML template file: {e}")
            raise

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
        """Loop thorugh all amendments in the new document and compare them
        against the same amendment in the old document (if possible),
        populate the various lists of changes"""

        self.added_and_removed_amdts(self.old_doc, self.new_doc)

        # for each amendment in the document
        # populate the star check, name changes and changes to existing amendments
        for key, new_amdt in self.new_doc.items():
            if key not in self.old_doc:
                # only the star check happens when there is no corespondind
                # amendment in previous document
                self.star_check(new_amdt, None)
                continue
            else:
                old_amend = self.old_doc[key]

                self.star_check(new_amdt, old_amend)
                self.diff_names(new_amdt, old_amend)
                self.diff_names_in_context(new_amdt, old_amend)
                self.diff_amdt_content(new_amdt, old_amend)

    def make_html(self):
        """Build up HTML document with various automated checks on amendments"""

        insert_point = self.html_root.find('.//div[@id="content-goes-here"]')
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
        removed_content = "Removed content: None"
        if self.removed_amdts:
            removed_content = (
                f"Removed content: {' '.join(self.removed_amdts)}"
                f" [total removed: {len(self.removed_amdts)}]"
            )
        added_content = "Added content: None"
        if self.added_amdts:
            added_content = (
                f"Added content: {' '.join(self.added_amdts)} "
                f"[total added: {len(self.added_amdts)}]"
            )

        card = templates.Card("Added and removed amendments")
        card.secondary_info.extend([E.P(added_content), E.P(removed_content)])
        # self.add_element_to_output_html(card.html)
        return card.html

        # add content to HTML template
        # self.add_elements_to_parent(
        #     "added-removed-amdts", [E.P(removed_content), E.P(added_content)]
        # )

    def render_added_and_removed_names(self) -> _Element:
        # ----------- Added and removed names section ----------- #
        # build up text content
        no_name_changes = "The following amendments have no name changes: None"
        if self.no_name_changes:
            no_name_changes = (
                "<p>The following amendments have no name changes: "
                f"{', '.join(self.no_name_changes)}"
                f" [total with no changes: {len(self.no_name_changes)}]</p>"
            )

        name_changes = html.fromstring(
            "<p>The following amendments have name changes: None</p>"
        )
        if self.name_changes:
            # name_changes = "The following amendments have name changes: "
            name_changes = E.TABLE(
                E.THEAD(
                    E.TR(
                        E.TH("Ref"),
                        E.TH("Names added"),
                        E.TH("Names removed"),
                        E.TH("Totals"),
                    )
                )
            )
            tbody = E.TBODY()
            name_changes.append(tbody)
            name_changes.classes.update(
                (
                    "sticky-head",
                    "an-table",
                    "table-responsive-md",
                    "table",
                )
            )

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
                # name_changes += f"<br>{item.num}: "
                total_added = len(item.added)
                total_removed = len(item.removed)
                totals = []
                if total_added:
                    totals.append(f"Added: {total_added}")
                if total_removed:
                    totals.append(f"Removed: {total_removed}")
                tr = E.TR(
                    E.TD(item.num),
                    E.TD(p_names_added),
                    E.TD(", ".join(item.removed)),
                    E.TD(html.fromstring(f"<p>{'<br>'.join(totals)}</p>")),
                )
                tbody.append(tr)

        # Name changes in context

        names_change_context_section = html.fromstring(
            '<section class="collapsible closed"><div'
            ' class="collapsible-header"><h3><span class="arrow"> </span>Name Changes'
            ' in Context <small class="text-muted"> [show]</small></h3><p>Expand this'
            " section to see the same names as above but in context.</p></div><div"
            ' class="collapsible-content" style="display: none;"'
            ' id="name-changes-in-context"></div></section>'
        )

        # build up text content
        changed_amdts = []
        if self.name_changes_in_context:
            changed_amdts.append(
                html.fromstring(
                    f"<p>The following {len(self.name_changes_in_context)} amendments"
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

        names_change_context_section.find(
            ".//div[@id='name-changes-in-context']"
        ).extend(changed_amdts)

        card = templates.Card("Added and removed names")
        card.secondary_info.extend(
            (
                name_changes,
                names_change_context_section,
            )
        )
        card.tertiary_info.append(html.fromstring(no_name_changes))
        # self.add_element_to_output_html(card.html)

        return card.html

        # add content to HTML template
        # self.add_elements_to_parent(
        #     "added-removed-names",
        #     [
        #         name_changes,
        #         names_change_context_section,
        #         html.fromstring(no_name_changes),
        #         # html.fromstring(name_changes),
        #     ],
        # )

    def render_stars(self) -> _Element:
        # -------------------- Star check section -------------------- #
        # build up text content
        correct_stars = "The following amendments have correct stars: None"
        if self.correct_stars:
            correct_stars = (
                "The following amendments have correct stars: "
                f"{', '.join(self.correct_stars)}"
                f" [total correct: {len(self.correct_stars)}]"
            )

        incorrect_stars = "The following amendments have incorrect stars: None"
        if self.incorrect_stars:
            incorrect_stars = (
                "The following amendments have incorrect stars: "
                f"{', '.join(self.incorrect_stars)}"
                f" [total incorrect: {len(self.incorrect_stars)}]"
            )

        card = templates.Card("Star Check")
        card.secondary_info.append(E.P(incorrect_stars))
        card.tertiary_info.append(E.P(correct_stars))
        # self.add_element_to_output_html(card.html)
        return card.html

    def render_changed_amdts(self) -> _Element:
        # -------------------- Changed Amendments -------------------- #
        # build up text content
        changed_amdts = (
            "<p>The following amendments have changed content:"
            " <strong>None</strong></p>"
        )
        if self.changed_amdts:
            changed_amdts = (
                f"<p>The following {len(self.changed_amdts)} amendments have changed"
                " content: </p>\n"
            )
            for item in self.changed_amdts:
                changed_amdts += f"<p class='h5'>{item.num}:</p>\n{item.html_diff}\n"

        card = templates.Card("Changed amendments")
        card.secondary_info.extend(html.fragments_fromstring(changed_amdts))

        return card.html

        # self.add_element_to_output_html(card.html)

        # add content to HTML template
        # self.add_elements_to_parent(
        #     "changed-amendments", html.fragments_fromstring(changed_amdts)
        # )

    def star_check(self, new_amdt: Amendment, old_amdt: Optional[Amendment]):
        """New amendments should have a black star.
        Amendments which previously had a black star should now have a white star.
        Amendments which previously had a white star should now have no star."""

        if old_amdt is None:
            # no previous document to compare against
            if new_amdt.star == "★":
                self.correct_stars.append(f"{new_amdt.num} ({new_amdt.star})")
            elif new_amdt.star == "☆":
                self.incorrect_stars.append(
                    f"{new_amdt.num} has white star (Black expected)"
                )
            elif not new_amdt.star:
                self.incorrect_stars.append(
                    f"{new_amdt.num} has no star (Black star expected)"
                )
            else:
                self.incorrect_stars.append(
                    f"Error in item {new_amdt.num} check manually."
                )

        else:
            if old_amdt.star == "★":
                # black star should have changed to white star
                if new_amdt.star == "☆":
                    self.correct_stars.append(f"{new_amdt.num} ({new_amdt.star})")

                elif new_amdt.star == "★":
                    self.incorrect_stars.append(
                        f"{new_amdt.num} has black star (White star expected)"
                    )
                elif not new_amdt.star:
                    self.incorrect_stars.append(
                        f"{new_amdt.num} has no star (White star expected)"
                    )

            if old_amdt.star == "☆":
                # white star should have changed to no star
                if not new_amdt.star:
                    self.correct_stars.append(f"{new_amdt.num} (no star)")

                elif new_amdt.star in ("★", "☆"):
                    star_state = "black star" if new_amdt.star == "★" else "white star"
                    self.incorrect_stars.append(
                        f"{new_amdt.num} has {star_state}. No star expected."
                    )
                else:
                    self.incorrect_stars.append(
                        f"Error in item {new_amdt.num} check manually."
                    )

    def added_and_removed_amdts(self, old_doc: "SupDocument", new_doc: "SupDocument"):
        """Return a tuple of sets containing the amendment numbers which have been added and removed

        You should call this method on the older document and pass in the newer document as the argument
        """

        self.removed_amdts = list(old_doc.amdt_set.difference(new_doc.amdt_set))
        self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

        # return removed_amdts, added_amdts

    def diff_names(self, new_amdt: Amendment, old_amdt: Amendment):
        # look for duplicate names. Only need to do this for the new_amdt.
        self.duplicate_names = find_duplicates(new_amdt.names)

        # if self.duplicate_names:
        #     logger.warning("Duplicate names found")

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
        new_amdt_heading = get_amdt_heading(new_amdt.xml)
        old_amdt_heading = get_amdt_heading(old_amdt.xml)

        if len(new_amdt_heading) == 0 or len(old_amdt_heading) == 0:
            logger.warning(f"{new_amdt.num}: no sponsors found")
            return
        else:
            new_amdt_heading = new_amdt_heading[0]
            old_amdt_heading = old_amdt_heading[0]

        dif_html_str = self._diff_xml_content(
            new_amdt_heading,
            old_amdt_heading,
            fromdesc=old_amdt.parent_doc.file_name,
            todesc=new_amdt.parent_doc.file_name,
        )
        if dif_html_str is not None:
            self.name_changes_in_context.append(ChangedAmdt(new_amdt.num, dif_html_str))

    def diff_amdt_content(self, new_amdt: Amendment, old_amdt: Amendment):
        new_amdt_content = get_amdt_content(new_amdt.xml)
        old_amdt_content = get_amdt_content(old_amdt.xml)

        if len(new_amdt_content) == 0 or len(old_amdt_content) == 0:
            logger.warning(f"{new_amdt.num}: no sponsors found")
            return
        else:
            new_amdt_content = new_amdt_content[0]
            old_amdt_content = old_amdt_content[0]

        dif_html_str = self._diff_xml_content(
            new_amdt_content,
            old_amdt_content,
            fromdesc=old_amdt.parent_doc.file_name,
            todesc=new_amdt.parent_doc.file_name,
        )
        if dif_html_str is not None:
            self.changed_amdts.append(ChangedAmdt(new_amdt.num, dif_html_str))

    def _diff_xml_content(
        self,
        new_xml: _Element,
        old_xml: _Element,
        fromdesc: str = "",
        todesc: str = "",
    ):
        """Return an HTML string containing tables showing the differences
        between coresponding amendments in each input document.

        Optionally pass in a function to narrow down the content to be diffed.
        the find_func must return an lxml.etree._Element"""

        # remove the unnecessary whitespace before comparing the text content
        old_text_content = text_content(clean_whitespace(old_xml))
        new_text_content = text_content(clean_whitespace(new_xml))

        if new_text_content == old_text_content:
            # no changes
            return

        fromlines = old_text_content.splitlines()
        tolines = new_text_content.splitlines()

        dif_html_str = html_diff.make_table(
            fromlines,
            tolines,
            fromdesc=fromdesc,
            todesc=todesc,
            context=True,
            numlines=3,
        )
        dif_html_str = dif_html_str.replace('nowrap="nowrap"', "")

        # remove nbsp but only when not in a span (as spans are used for changes
        # e.g. <span class="diff_sub">) and not if this nbsp is folowed by
        # another nbsp (as this is used for indentation)
        dif_html_str = nbsp.sub(" ", dif_html_str)

        return dif_html_str


def main():
    if len(sys.argv) > 1:
        # do cmd line version
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

        args = parser.parse_args(sys.argv[1:])

        filename = "html_diff.html"
        report = Report(args.old_doc, args.new_doc)
        report.html_tree.write(
            filename,
            encoding="utf-8",
            doctype="<!DOCTYPE html>",
        )
        webbrowser.open(Path(filename).resolve().as_uri())

    else:
        # could do GUI version here
        print("No arguments given")
        return


def find_duplicates(lst: list[str]) -> list[str]:
    # Convert the list to a set to remove duplicates
    unique_items = set(lst)

    # If the length of the set is less than the length of the list,
    # then there are duplicates
    if len(unique_items) < len(lst):
        # Convert the set back to a list and sort it
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


def clean_whitespace(parent_element: _Element) -> _Element:
    """remove unwanted whitespace from parent_element and all its descendant
    elements. Note: parent_element is modified in place.
    Add a newline after parent_elements (which represent paragraphs)"""

    for element in parent_element.iter("*"):
        tag = QName(element).localname

        if tag in (
            "b",
            "i",
            "a",
            "u",
            "sub",
            "sup",
            "abbr",
            "span",
        ):
            # these are inline elements, we should leave them well alone
            # I think defined here:
            # https://docs.oasis-open.org/legaldocml/akn-core/v1.0/cos01/part2-specs/schemas/akomantoso30.xsd
            # //xsd:schema/xsd:group[@name="HTMLinline"]/xsd:choice
            continue

        # remove whitespace
        if element.text:
            element.text = element.text.strip()
        if element.tail:
            element.tail = element.tail.strip()

        # Add in newlines after each of these elements
        if tag in (
            # "mod",
            "p",
            "docIntroducer",
            "docProponent",
            "heading",
        ) or (tag == "block" and element.get("name") == "instruction"):
            try:
                last_child = element[-1]
            except IndexError:
                last_child = None

            if last_child is not None:
                # add test for this.
                if last_child.tail:
                    last_child.tail = f"{last_child.tail}\n"
                else:
                    last_child.tail = "\n"
            else:
                element.text = f"{element.text}\n"

        # Add in tab after num element
        if tag == "num":
            if element.text:
                element.text = f"{element.text}\t"

    return parent_element


if __name__ == "__main__":
    main()
