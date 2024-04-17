#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
import webbrowser
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from tempfile import mkstemp
from typing import NamedTuple

from lxml import etree, html
from lxml.etree import _Element

from lawchecker.lawchecker_logger import logger
from lawchecker import templates
from lawchecker import xpath_helpers as xp
from lawchecker.compare_bill_numbering import CompareBillNumbering
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, NSMAP, NSMAP2, PARSER
from lawchecker.utils import diff_xml_content


class ChangedSect(NamedTuple):
    guid: str
    old_num: str
    new_num: str
    html_diff: str

class Section:
    # section includes clauses (aka sections) and schedules
    def __init__(
        self, item: _Element,
        parent_doc: "Bill",
        schedule_number: str = "",
    ):

        self.parent_doc = parent_doc

        self.xml = item

        self.guid = item.get("GUID", default="")
        if not self.guid:
            raise ValueError("GUID is None")

        self.num = item.findtext("./xmlns:num", namespaces=NSMAP, default="No number")

        if schedule_number:
            # get the schedule number
            self.num = f"{schedule_number} p {self.num}"
        else:
            self.num = f"C {self.num}"

        # for sorting
        self._sort_list: list[str | int] = []
        for x in self.num.split(" "):
            try:
                self._sort_list.append(int(x))
            except ValueError:
                self._sort_list.append(x)

    def __lt__(self, other):
        return self._sort_list < other._sort_list

    def __eq__(self, other):
        return self._sort_list == other._sort_list


class Bill(Mapping):
    """Container for an Bill document"""

    def __init__(self, xml: Path | _Element):
        if isinstance(xml, Path):
            self.file_name = xml.name
            self.file_path = str(xml.resolve())
            tree = etree.parse(self.file_path, parser=PARSER)
            self.root = tree.getroot()
            logger.info(f"Loaded {self.file_name}")
        else:
            self.file_name = "Test"
            self.file_path = "test/Test"
            tree = etree.ElementTree(xml)
            self.root = xml

        # self.root = remove_pis(self.root)

        # build up metadata
        self.meta_bill_title: str
        self.meta_pub_date: str

        self.get_meta_data()

        self.problem_sections = 0
        self.sections: list[Section] = []

        for sect_xml in xp.get_sections(self.root):
            try:
                section = Section(sect_xml, self)
                self.sections.append(section)
            except ValueError as e:
                logger.warning(repr(e))
                self.problem_sections += 1

        for schedules_xml in xp.get_schedules(self.root):

            schedule_number = schedules_xml.findtext("xmlns:num", namespaces=NSMAP)
            if not schedule_number:
                schedule_number = "No number"
            else:
                schedule_number = schedule_number.replace("Schedule", "S")

            for schedule_paragraphs in xp.get_sched_paras(schedules_xml):
                try:
                    section = Section(schedule_paragraphs, self, schedule_number)
                    self.sections.append(section)
                except ValueError as e:
                    logger.warning(repr(e))
                    self.problem_sections += 1

        self._dict = self._create_sect_map()
        self.amdt_set = set(self._dict.keys())

    def get_meta_data(self):

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
            published_xp = ".//FRBRManifestation/FRBRdate[@name='published']"
            published: _Element = self.root.find(published_xp, namespaces=NSMAP2)  # type: ignore

            published_date = published.get("date", default="").split("T")[0]
            self.meta_pub_date = datetime.strptime(
                published_date, "%Y-%m-%d"  # type: ignore
            ).strftime("%A %d %B %Y")
        except Exception:
            warning_msg = f"Can't find Published Date meta data. Check {self.file_name}"
            self.meta_pub_date = warning_msg
            # logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

    def _create_sect_map(self) -> dict[str, Section]:
        _sect_map: dict[str, Section] = {}

        for section in self.sections:
            if section.guid in _sect_map:
                logger.warning(f"Duplicate guid: {section.guid}")
            _sect_map[section.guid] = section

        return _sect_map

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
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE.resolve())
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f"Error parsing HTML template file: {e}")
            raise

        self.days_between_papers = days_between_papers

        self.old_doc = Bill(old_file)
        self.new_doc = Bill(new_file)

        self.removed_sects: list[Section] = []
        self.added_sects: list[Section] = []

        self.changed_sects: list[ChangedSect] = []

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

        self.added_and_removed_sects(self.old_doc, self.new_doc)

        # for each amendment in the document
        # populate the star check, name changes and changes to existing amendments
        for key, new_sect in self.new_doc.items():
            if key not in self.old_doc:
                continue

            old_amend = self.old_doc[key]

            self.diff_sect_content(new_sect, old_amend)

    def make_html(self):
        """
        Build up HTML document with various automated checks on bills
        """

        try:
            # change the title
            self.html_root.find('.//title').text = "Compare Bills"  # type: ignore
            self.html_root.find('.//h1').text = "Compare Bills"  # type: ignore
        except Exception:
            pass

        insert_point: _Element = self.html_root.find('.//div[@id="content-goes-here"]')  # type: ignore
        insert_point.extend(
            (
                self.render_intro(),
                self.render_added_and_removed_sect(),
                self.render_changed_sects(),
                self.render_numbering_changes(),
            )
        )

    def render_intro(self) -> _Element:
        # ------------------------- intro section ------------------------ #
        into = (
            "This report summarises changes between the XML of two LawMaker"
            " Bill versions. The bill documents are:"
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

    def render_added_and_removed_sect(self) -> _Element:
        # ----------- Removed and added amendments section ----------- #

        # create spans with section number add guid as tooltip.
        span_template = '<span class="col-12 col-sm-6 col-md-4 col-lg-3" data-toggle="tooltip" title="{guid}">{num}</span> '
        removed_spans = [
            span_template.format(guid=x.guid, num=x.num) for x in self.removed_sects
        ]
        added_spans = [
            span_template.format(guid=x.guid, num=x.num) for x in self.added_sects
        ]

        # build up text content
        removed_content = "Removed content: <strong>None</strong>"
        if self.removed_sects:

            removed_content = (
                f"<p class='h5'>Removed content: <span class='red'>{len(self.removed_sects)}</span><br />"
                f"<div class='row'>{''.join(removed_spans)}</div><br />"
            )
        added_content = "Added content: <strong>None</strong>"
        if self.added_sects:
            added_content = (
                f"<p class='h5'>Added content: <span class='red'>{len(self.added_sects)}</span><br /></p>"
                f"<div class='row'>{''.join(added_spans)}</div><br />"
            )

        card = templates.Card("Added and removed clauses and schedule paragraphs")
        card.secondary_info.extend([
            html.fromstring(f"<div>{added_content}</div>"),
            html.fromstring(f"<div>{removed_content}</div>")
        ])
        return card.html


    def render_changed_sects(self) -> _Element:
        # -------------------- Changed Sections -------------------- #
        # build up text content
        changed_sects = (
            "<p><strong>Zero</strong> clauses or schedule paragraphs have changed content.</p>"
        )
        if self.changed_sects:
            changed_sects = (
                f'<p><strong class="red">{len(self.changed_sects)}</strong>'
                " clauses or schedule paragraphs have changed content: </p>\n"
            )

            html_diffs: str = ""
            grid_element = html.Element('div')
            grid_element.classes.add('row')
            for i, item in enumerate(self.changed_sects):
                num_span = etree.SubElement(grid_element, 'span')
                num_span.classes.update(('col-12', "col-sm-6", "col-md-4", "col-lg-3"))
                anchor = etree.SubElement(num_span, 'a', attrib={"href": f"#diff-table-{i}"})
                anchor.classes.add('hidden-until-hover')
                if item.old_num == item.new_num:
                    anchor.text = item.old_num
                else:
                    anchor.text = f"{item.old_num} [{item.new_num}]"

                # changed_nums += f"{item.num}<br/>\n"
                html_diffs += f"<br/><div id=diff-table-{i}>{item.html_diff}</div>\n"

            changed_sects += html.tostring(grid_element, encoding=str) + html_diffs

        card = templates.Card("Changed clauses  or schedule paragraphs")
        info = ("<p>Listed below are any Clauses or Schedule paragraphs with changed content."
                " The items are listed with their number from the old bill and if changed, the"
                " number from the new bill in square brackets. Clicking on each item will take"
                " you to a table showing the changes in context.</p>")
        card.secondary_info.extend(html.fragments_fromstring(info + changed_sects))
        b = set()
        b.update
        return card.html

    def render_numbering_changes(self) -> _Element:

        _bill_renumbering = CompareBillNumbering(
            [
                (self.old_doc.root, self.old_doc.file_name),
                (self.new_doc.root, self.new_doc.file_name),
            ]
        )

        # we only expect one table but the to_html method returns a list of tables...
        bill_numbering_html_tables = '\n'.join(_bill_renumbering.to_html())

        bill_numbering_html_tables = re.sub(r"sec_(\d+)", r"C \1", bill_numbering_html_tables)
        bill_numbering_html_tables = re.sub(r"sched_", "S ", bill_numbering_html_tables)
        bill_numbering_html_tables = re.sub(r"__para_?", " p ", bill_numbering_html_tables)
        bill_numbering_html_tables = re.sub(r"([a-z])_([a-z])", r"\1 \2", bill_numbering_html_tables)

        card = templates.Card("Clauses or schedule paragraphs numbering changes")
        info = ("<p>Each clause and schedule paragraph has a GUID (or global unique identifier)"
                " which should stay the same even as a bill is renumbered. The table below "
                "shows any changes in the numbering (of each clause or schedule paragraph) "
                "between the two bills.</p>")
        card.secondary_info.extend(
            # html.fromstring('<div>' + '\n'.join(_bill_renumbering.to_html()) + '</div>')
            html.fragments_fromstring(info + bill_numbering_html_tables)
        )

        return card.html



    def added_and_removed_sects(self, old_doc: "Bill", new_doc: "Bill"):

        """Find the amendment numbers which have been added and removed"""

        removed_guids = list(old_doc.amdt_set.difference(new_doc.amdt_set))
        added_guids = list(new_doc.amdt_set.difference(old_doc.amdt_set))

        self.removed_sects = [old_doc[guid] for guid in removed_guids]
        self.removed_sects.sort()
        self.added_sects = [new_doc[guid] for guid in added_guids]
        self.added_sects.sort()

        # return removed_sects, added_sects


    def diff_sect_content(self, new_sect: Section, old_sect: Section):

        """
        Create an HTML string containing a tables showing the differences
        between old_sect//amendmentContent and new_sect//amendmentContent.

        amendmentContent is the element which contains the text of the
        amendment. It does not contain the sponsor information.
        """


        dif_html_str = diff_xml_content(
            new_sect.xml,
            old_sect.xml,
            # fromdesc=old_sect.parent_doc.file_name,
            # todesc=new_sect.parent_doc.file_name,
            fromdesc=f"Old bill: {old_sect.num}",
            todesc=f"New bill: {new_sect.num}",
        )
        if dif_html_str is not None:
            self.changed_sects.append(
                ChangedSect(new_sect.guid, old_sect.num, new_sect.num, dif_html_str)
            )
            # print(f"{new_sect.guid=}\n{new_sect.num=}\n{dif_html_str=}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Create an HTML report comparing LawMaker bill versions."
        )
    )

    parser.add_argument(
        "old_bill",
        type=Path,
        help="A LawMaker bill XML document you wish to compare from",
    )

    parser.add_argument(
        "new_bill",
        type=Path,
        help="A LawMaker bill XML document you wish to compare to",
    )

    parser.add_argument(
        "-c",
        "--vscode-diff",
        action="store_true",
        help="Also diff a plain text version of the XML files in vscode",
    )

    args = parser.parse_args(sys.argv[1:])

    filename = "html_diff.html"

    report = Report(
        args.old_bill,
        args.new_bill,
    )

    report.html_tree.write(
        filename,
        encoding="utf-8",
        doctype="<!DOCTYPE html>",
    )

    webbrowser.open(Path(filename).resolve().as_uri())

    if args.vscode_diff:

        diff_in_vscode(report.old_doc.root, report.new_doc.root)

def diff_in_vscode(old_doc: _Element, new_doc: _Element):

    cleaned_bill_1 = clean_bill_xml(old_doc)
    cleaned_bill_2 = clean_bill_xml(new_doc)

    _, _temp_1_path = mkstemp(suffix=".txt", prefix="Bill1_", text=True)
    _, _temp_2_path = mkstemp(suffix=".txt", prefix="Bill2_", text=True)

    temp_1_Path = Path(_temp_1_path).resolve()
    temp_2_Path = Path(_temp_2_path).resolve()

    # output cleaned files
    # with open("temp_1_Path.txt", 'w', encoding='utf-8') as f:
    with open(temp_1_Path, 'w', encoding='utf-8') as f:
        f.write(cleaned_bill_1)
    with open(temp_2_Path, 'w', encoding='utf-8') as f:
        f.write(cleaned_bill_2)

    subprocess_args = ["code", "--diff", str(temp_1_Path.resolve()), str(temp_2_Path.resolve())]
    # print(subprocess_args)

    # subprocess_cmd = f'code --diff "{temp_1_Path.resolve()}" "{temp_2_Path.resolve()}"'

    if sys.platform == 'win32':
        # for some reason shell=True is needed on Windows
        subprocess.run(subprocess_args, shell=True)
    else:
        subprocess.run(subprocess_args, shell=False)


def clean_bill_xml(bill_xml: _Element):
    # get the body
    body: _Element = bill_xml.find('.//xmlns:body', namespaces=NSMAP)  # type: ignore

    # remove newlines after num elements
    for num in body.iter('{*}num'):
        if num.tail:
            num.tail = num.tail.replace('\n', ' ')

    # # remove whitespace around processing instructions
    # for pi in body.iter(ProcessingInstruction):
    #     if pi.tail:
    #         pi.tail = pi.tail.strip()

    body_text: str = body.xpath('string()')  # type: ignore

    return clean_text(body_text)


def clean_text(body_text: str) -> str:
    # clean the body
    t = re.sub(r'^ +', '', body_text, flags=re.MULTILINE)
    t = re.sub(r'^(\([a-zA-Z0-9]+\)) +\n+', r'\1 ', t, flags=re.MULTILINE)
    # schedule paragraphs start with a number but no brackets
    t = re.sub(r'^(\d+) +\n+', r'\1 ', t, flags=re.MULTILINE)
    t = re.sub(r'\n\n+', '\n', t)
    t = re.sub(r'  +', ' ', t)

    return t


if __name__ == '__main__':
    main()
