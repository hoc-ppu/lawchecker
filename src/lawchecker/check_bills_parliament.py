import json
import sys
import webbrowser
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

import requests
from lxml import etree, html
from lxml.etree import QName, _Element, iselement
from lxml.html import HtmlElement

from lawchecker import templates, utils
from lawchecker import xpath_helpers as xp
from lawchecker.compare_amendment_documents import ChangedAmdt, ChangedNames
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, NSMAP, NSMAP2, UKL

JSON = int | str | float | bool | None | list["JSON"] | dict[str, "JSON"]
JSONObject = dict[str, JSON]
JSONList = list[JSON]
JSONType = JSONObject | JSONList


class ContainerType(StrEnum):
    COMMITTEE_DECISIONS = "Committee Stage Decisions"
    AMENDMENT_PAPER = "Amendment Paper"
    AMDTS_FROM_API = "Amendments from API"
    UNKNOWN = "Unknown"


def get_container_type(string: str) -> ContainerType:
    string = string.casefold().strip()

    for container_type in ContainerType:
        if container_type.casefold() in string:
            return container_type

    return ContainerType.UNKNOWN


class InvalidDataError(ValueError):
    """Exception raised for errors in the input JSON data."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def progress_bar(iterable: Iterable, total: int) -> list:
    output = []
    count = 0
    bar_len = 50
    for item in iterable:
        output.append(item)
        count += 1
        filled_len = int(round(bar_len * count / total))
        percents = round(100.0 * count / total, 1)
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        sys.stdout.write(f"[{bar}] {percents}%\r")
        sys.stdout.flush()

    return output


def request_json(url: str) -> dict:
    response = requests.get(url)
    return response.json()


class Sponsor:
    def __init__(
        self,
        name: str,
        member_id: int,
        is_lead: bool,
        sort_order: int,
    ):

        self.name = name
        self.is_lead = is_lead
        self.sort_order = sort_order
        self.member_id = member_id

    def __eq__(self, other: "Sponsor") -> bool:
        if not isinstance(other, Sponsor):
            return NotImplemented
        return (
            self.name == other.name
            and self.member_id == other.member_id
            and self.is_lead == other.is_lead
            and self.sort_order == other.sort_order
        )

    def __lt__(self, other: "Sponsor") -> bool:
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @classmethod
    def from_json(cls, sponsor: dict[str, Any]) -> "Sponsor":

        name: str | None = sponsor.get("name", None)
        member_id: int | None = sponsor.get("memberId", None)
        is_lead: bool | None = sponsor.get("isLead", None)
        sort_order: int | None = sponsor.get("sortOrder", None)

        if any((i is None for i in (name, member_id, is_lead, sort_order))):
            raise InvalidDataError(
                "Error: Sponsor JSON data is invalid or missing required fields"
            )

        return cls(name, member_id, is_lead, sort_order)  # type: ignore

    @classmethod
    def from_supporters_xml(cls, supporters: list[_Element]) -> list["Sponsor"]:
        # from <block name="supporters">
        sponsors: list[Sponsor] = []

        for i, element in enumerate(supporters, start=1):
            # is_lead = i == 1
            tag = QName(element).localname
            if tag not in ("docProponent", "docIntroducer"):
                logger.info(f"Unexpected tag {tag} in supporters block")
                continue

            is_lead = tag == "docIntroducer"

            refers_to = element.get("refersTo")
            if not refers_to:
                logger.error("docProponent element has no refersTo attribute")
                continue
            try:
                mnis_id = int(refers_to.split("-")[-1])
            except (IndexError, ValueError):
                logger.error(
                    "docProponent refersTo attribute is not in the expected format"
                )
                continue
            if not element.text:
                logger.error("docProponent element has no text")
                continue
            member_from = element.text.strip()

            sponsors.append(cls(member_from, mnis_id, is_lead, i))

        return sponsors


class Amendment:
    def __init__(
        self,
        amendment_text: str,
        explanatory_text: str,
        amendment_number: str,
        decision: str,
        sponsors: list[Sponsor],
        parent: "AmdtContainer | None" = None,
    ):

        self.amendment_text = amendment_text
        self.explanatory_text = explanatory_text
        self.num: str = amendment_number
        self.decision: str = decision
        self.sponsors: list[Sponsor] = sponsors
        self.parent: "AmdtContainer | None" = parent

        # we might need to come up with an amendment id that is the same for both
        # the API and the XML... in particular a problem with amendments to amendments

    def __eq__(self, other: "Amendment") -> bool:
        if not isinstance(other, Amendment):
            return NotImplemented
        return (
            self.amendment_text == other.amendment_text
            and self.explanatory_text == other.explanatory_text
            and self.num == other.num
            and self.decision == other.decision
            and self.sponsors == other.sponsors
        )

    @classmethod
    def from_json(cls, amendment_json: dict, parent: "AmdtContainer | None" = None) -> "Amendment":

        amendment_text_gen = (
            f'{t.get("hangingIndentation", "") or ""} {t.get("text", "")}'.strip()
            for t in amendment_json.get("amendmentLines", [])
        )
        amendment_text = "\n".join(amendment_text_gen)

        explanatory_text = amendment_json.get("explanatoryText", "")

        # example amendmentNote: "As an Amendment to Kim Leadbeater’s proposed Amendment 186:—"
        # self.amendment_note: str | None = amendment_json.get(
        #     "amendmentNote", None
        # )  # do we need this?

        # self.main_header: str = amendment_json.get("mainHeader", "")

        # self.amendment_id: int | None = amendment_json.get("amendmentId", None)

        # self.amendment_type: str = amendment_json.get("amendmentType", "")
        # self.clause: int | None = amendment_json.get("clause", None)
        # self.schedule: int | None = amendment_json.get(
        #     "clause", None
        # )  # will this be an int?
        amendmet_number: str = amendment_json.get(
            "marshalledListText", ""
        )  # amendment_no
        decision: str = amendment_json.get("decision", "")
        # self.decision_explanation: str = amendment_json.get("decisionExplanation", "")
        sponsors = [
            Sponsor.from_json(item) for item in amendment_json.get("sponsors", [])
        ]

        return cls(
            amendment_text, explanatory_text, amendmet_number, decision, sponsors, parent
        )

    @classmethod
    def from_xml(cls, amendment_xml: _Element, parent: "AmdtContainer | None" = None) -> "Amendment":
        # assume amendment_xml is an amendmentBody element

        # get the decision
        decision_block = amendment_xml.xpath(
            './/xmlns:block[@name="decision"]', namespaces=NSMAP
        )
        decision = ""
        if not decision_block:
            decision = utils.normalise_text(xp.text_content(decision_block[0]))

        #  get the amendment number
        try:
            e_id = amendment_xml.xpath("xmlns:amendment/xmlns:amendmentBody/@eId", namespaces=NSMAP)[0]
            amdt_no = e_id.split("_")[-1]
        except Exception:
            print("Warning no amendment number found")
            amdt_no = ""

        # get the sponsors
        # proposer = xp.get_doc_introducer(amendment_xml)
        # supporters = xp.get_doc_proponents(amendment_xml)
        sponsors = Sponsor.from_supporters_xml(xp.get_name_elements_2(amendment_xml))

        # get the explanatory text
        explanatory_text_ps = amendment_xml.xpath(
            './/xmlns:amendmentJustification/xmlns:blockContainer[class="explanatoryStatement"]/xmlns:p',
            namespaces=NSMAP,
        )
        explanatory_text = "\n".join(xp.text_content(p) for p in explanatory_text_ps)

        # get amendment text
        try:
            amendment_content = xp.get_amdt_content_2(amendment_xml)[0]
        except IndexError:
            logger.error("No amendment content found")
            raise

        try:
            amendment_num = amendment_content.find(
                ".//xmlns:num[@ukl:dnum]", namespaces=NSMAP
            )
            amendment_num.getparent().remove(amendment_num)  # type: ignore
        except Exception as e:
            logger.error(
                f"Can't remove amendment number from amendment content {repr(e)}"
            )

        add_quotes_to_quoted_structures(amendment_content)

        amendment_text = utils.normalise_text(
            xp.text_content(utils.clean_whitespace(amendment_content))
        )

        return cls(amendment_text, explanatory_text, amdt_no, decision, sponsors, parent)


def normalise_amendments_xml(amendment_xml: _Element) -> _Element:
    raise NotImplementedError


def add_quotes_to_quoted_structures(amendment_element: _Element) -> None:

    """Element is modified in place"""

    # get the text
    # if there is a quoted structure there could be strangeness with quotes
    quoted_elements: list[_Element] = amendment_element.xpath(
        ".//xmlns:*[@ukl:endQuote or @ukl:startQuote or @endQuote or @startQuote]", namespaces=NSMAP
    )
    print(f"Quoted Elements: {len(quoted_elements)}")
    for qs in quoted_elements:
        tag = QName(qs).localname
        if tag == "def":
            print(f"Def: {qs.text}")
            print(qs.attrib)
        if qs.get("startQuote") == "“" or qs.get(f"{{{UKL}}}startQuote") == "“":

            if qs.text:
                qs.text = f'“{qs.text}'
                print("here 1")
            else:
                qs.text = "“"
        if qs.get("endQuote") == "”" or qs.get(f"{{{UKL}}}endQuote") == "”":
            if tag == "quotedStructure":
                if qs.tail:
                    qs.tail = f'”{qs.tail}'
                else:
                    qs.tail = "”"
            else:
                if qs.text:
                    qs.text = f'{qs.text}”'
                    print("here 2")
                else:
                    qs.text = "”"



class AmdtContainer(Mapping):
    """Container for an amendment document aka official list"""

    def __init__(
        self,
        amendments: list[Amendment],
        container_type: ContainerType = ContainerType.UNKNOWN,
        bill_title: str = "Unknown Bill Title",
        pub_date: str = "Unknown Published Date",
        resource_identifier: str = "Unknown",
    ):

        # move this to the javascript
        # self.short_file_name = utils.truncate_string(self.file_name).replace(".xml", "")

        # defaults for metadata
        self.meta_container_type: ContainerType = container_type
        self.meta_bill_title: str = bill_title
        self.meta_pub_date: str = pub_date

        self.amendments = amendments
        self.resource_identifier = resource_identifier

        self._dict = self._create_amdt_map()
        self.amdt_set = set(amdt.num for amdt in self.amendments)

    @classmethod
    def blank_container(cls) -> "AmdtContainer":
        return cls([])

    @classmethod
    def from_json(
        cls,
        json_data: list[JSONType],
        container_type: ContainerType = ContainerType.AMDTS_FROM_API,
        resource_identifier: str = "Api Amendments",
    ) -> "AmdtContainer":

        amendments: list[Amendment] = []

        for amendment in json_data:
            try:
                amendment = Amendment.from_json(amendment)
                amendments.append(amendment)
            except InvalidDataError as e:
                logger.warning(repr(e))

        return cls(
            amendments,
            container_type=container_type,
            resource_identifier=resource_identifier,
        )

    @classmethod
    def from_xml_element(
        cls,
        xml_element: _Element,
        container_type: ContainerType = ContainerType.UNKNOWN,
        resource_identifier: str = "Test",
    ) -> "AmdtContainer":

        amendments: list[Amendment] = []

        for amdt_xml in xp.get_amendments(xml_element):
            try:
                # TODO: fix this
                amendment = Amendment.from_xml(amdt_xml)
                amendments.append(amendment)
            except ValueError as e:
                logger.warning(repr(e))

        amdt_container = cls(
            amendments,
            container_type=container_type,
            resource_identifier=resource_identifier,
        )

        # override default metadata
        amdt_container.get_meta_data_from_xml(xml_element)

        return amdt_container

    @classmethod
    def from_xml_file(cls, xml_file: Path) -> "AmdtContainer":

        resource_identifier = xml_file.name  # important
        file_path = str(xml_file.resolve())  # should this be location
        tree = etree.parse(file_path)
        root = tree.getroot()

        return cls.from_xml_element(
            root,
            resource_identifier=resource_identifier,
        )


    def get_meta_data_from_xml(self, root_element: _Element) -> None:
        try:
            list_type_text: str = root_element.findtext(".//block[@name='listType']", namespaces=NSMAP2)  # type: ignore
            self.meta_container_type = get_container_type(list_type_text)
            # self.meta_list_type = list_type.text  # type: ignore

        except Exception as e:
            warning_msg = f"Can't find List Type meta data. Check {self.resource_identifier}"
            # self.meta_list_type = warning_msg  # should we add this back in?
            logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

        try:
            print(len(root_element.xpath("//xmlns:TLCConcept", namespaces=NSMAP)))
            bill_title = root_element.xpath(
                # TODO: if this works add it to the compare amendments documents
                "//xmlns:TLCConcept[@eId='varBillTitle']/@showAs", namespaces=NSMAP
            )
            # don't use .get here  as that defaults to None
            # self.meta_bill_title = bill_title.attrib["showAs"]  # type: ignore
            self.meta_bill_title: str = bill_title[0]
            # [x] test
        except Exception as e:
            print(repr(root_element))
            warning_msg = f"Can't find Bill Title meta data. Check {self.resource_identifier}"
            self.meta_bill_title = warning_msg
            logger.warning(f"Problem parsing XML. {warning_msg}: {repr(e)}")

        try:
            # add a test for this
            published_date = root_element.find(
                ".//FRBRManifestation/FRBRdate[@name='published']", namespaces=NSMAP2
            )
            self.meta_pub_date = datetime.strptime(
                published_date.get("date", default=""), "%Y-%m-%d"  # type: ignore
            ).strftime("%A %d %B %Y")

        except Exception as e:
            warning_msg = f"Can't find Published Date meta data. Check {self.resource_identifier}"
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
    Container for Amendments API Report.

    This report checks for differences between the amendments in the bills API
    and the amendments in the LawMaker XML official list document (proceedings
    or amendment paper).
    """

    def __init__(
        self,
        xml: Path | _Element,
        json_amdts: list[JSONType],
    ):
        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f"Error parsing HTML template file: {e}")
            raise

        # create AmdtContainer object for xml amendments
        if isinstance(xml, Path):
            self.xml_amdts = AmdtContainer.from_xml_file(xml)
        elif iselement(xml):
            self.xml_amdts = AmdtContainer.from_xml_element(xml)
        else:
            raise TypeError("xml must be a Path or an Element")

        # create AmdtContainer object for json amendments
        self.json_amdts = AmdtContainer.from_json(json_amdts)

        self.not_in_api: list[str] = []
        self.incorrect_in_api: list[str] = []
        self.incorrect_decision: list[str] = []

        self.missing_api_amdts: list[str] = []
        self.missing_bill_amdts: list[str] = []

        self.no_name_changes: list[str] = []
        self.name_changes: list[ChangedNames] = []
        # self.duplicate_names: list[str] = []
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

        self.added_and_removed_amdts(self.xml_amdts, self.json_amdts)

        # for each amendment in the document
        # populate the star check, name changes and changes to existing amendments
        for key, xml_amdt in self.xml_amdts.items():

            if key not in self.json_amdts:
                # the star check only happens when there is no coresponding
                # amendment in previous document
                # self.star_check(new_amdt, None)
                continue

            json_amend = self.json_amdts[key]

            self.diff_names(xml_amdt, json_amend)
            self.diff_names_in_context(xml_amdt, json_amend)
            self.diff_amdt_content(xml_amdt, json_amend)

    def make_html(self):
        """
        Build up HTML document with various automated checks on amendments
        """

        try:
            # change the title
            self.html_root.find('.//title').text = "Check Amendments"  # type: ignore
            self.html_root.find('.//h1').text = "Check Amendments on Bills.parliament"  # type: ignore
        except Exception:
            pass

        xp = './/div[@id="content-goes-here"]'
        insert_point: HtmlElement = self.html_root.find(xp)  # type: ignore
        # print(etr)
        insert_point.extend(
            (
                self.render_intro(),
                self.render_missing_amdts(),
                self.render_added_and_removed_names(),
                self.render_changed_amdts(),
            )
        )

    def render_intro(self) -> HtmlElement:
        # ------------------------- intro section ------------------------ #
        into = (
            "This report summarises differences between amendments in the "
            "bills API and the amendments in the LawMaker document"
            " XML official list documents. The document is:"
            f"<br><strong>{self.xml_amdts.meta_bill_title}</strong>"
        )

        meta_data_table = templates.Table(
            ("", self.xml_amdts.meta_bill_title)
        )

        # meta_data_table.add_row(
        #     ("File path", self.xml_amdts.file_path)
        # )
        meta_data_table.add_row(
            ("Bill Title", self.xml_amdts.meta_bill_title)
        )
        meta_data_table.add_row(
            ("Published date", self.xml_amdts.meta_pub_date)
        )
        meta_data_table.add_row(
            ("List Type", self.xml_amdts.meta_container_type)
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

    def render_missing_amdts(self) -> HtmlElement:
        # ----------- Removed and added amendments section ----------- #
        # build up text content
        removed_content = "Missing amendments: <strong>None</strong>"
        if self.removed_amdts:
            removed_content = (
                f"Missing content: <strong>{len(self.removed_amdts)}</strong><br />"
                f"{' '.join(self.removed_amdts)}"
            )

        info = (
            "<p>Listed below are any Amendments (& New Clauses etc.) which are"
            " present in the XML from LawMaker but not present in Amendments"
            " avaliable via the API. This means that they are almost certainly"
            " also missing from bills.parliament. </p>"
        )

        card = templates.Card("Missing amendments")
        card.secondary_info.extend(
            # html.fromstring(f"<p>{added_content}</p>"),
            html.fragments_fromstring(
                f"{info}<p>{removed_content}</p>",
                no_leading_text=True
            )
        )
        return card.html

    def added_and_removed_names_table(self) -> HtmlElement:

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
            p_names_added = html.fromstring('<p class="row"></p>')
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

    def render_added_and_removed_names(self) -> HtmlElement:

        """Added and removed names section"""

        no_name_changes = html.fromstring(
            "<p><strong>Zero</strong> amendments have no name changes.</p>"
        )

        if self.no_name_changes:

            sec = (templates.SmallCollapsableSection(
                f"<span><strong>{len(self.no_name_changes)}</strong>"
                f" amendments have correct names: "
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

    def render_changed_amdts(self) -> HtmlElement:
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
        card.secondary_info.extend(
            html.fragments_fromstring(changed_amdts, no_leading_text=True)
        )

        return card.html

    def added_and_removed_amdts(self, old_doc: "AmdtContainer", new_doc: "AmdtContainer"):

        """Find the amendment numbers which have been added and removed"""

        self.removed_amdts = list(old_doc.amdt_set.difference(new_doc.amdt_set))
        self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

        # return removed_amdts, added_amdts

    def diff_names(self, new_amdt: Amendment, old_amdt: Amendment):
        # look for duplicate names. Only need to do this for the new_amdt.
        self.duplicate_names = find_duplicate_sponsors(new_amdt.sponsors)

        if self.duplicate_names:
            # warn in UI
            logger.warning(f"Duplicate names found in {new_amdt.num}")

        added_names = [item.name for item in new_amdt.sponsors if item not in old_amdt.sponsors]
        removed_names = [item.name for item in old_amdt.sponsors if item not in new_amdt.sponsors]

        if not added_names and not removed_names:
            # there have been no name changes
            self.no_name_changes.append(new_amdt.num)
        else:
            self.name_changes.append(
                ChangedNames(new_amdt.num, added_names, removed_names)
            )

    def diff_names_in_context(self, xml_amdt: Amendment, api_amdt: Amendment):

        """
        Create an HTML string containing a tables showing the differences
        between the sponsors of xml amendments and api amendments.
        """

        fromlines = [sponsor.name for sponsor in xml_amdt.sponsors]
        tolines = [sponsor.name for sponsor in api_amdt.sponsors]

        dif_html_str = utils.html_diff_lines(
            fromlines,
            tolines,
            fromdesc="Lawmaker XML",
            todesc="Bills API",
        )

        if dif_html_str is not None:
            self.name_changes_in_context.append(ChangedAmdt(xml_amdt.num, dif_html_str))

    def diff_amdt_content(self, new_amdt: Amendment, old_amdt: Amendment):

        """
        Create an HTML string containing a tables showing the differences
        between old_amdt//amendmentContent and new_amdt//amendmentContent.

        amendmentContent is the element which contains the text of the
        amendment. It does not contain the sponsor information.
        """

        new_amdt_content = new_amdt.amendment_text.split("\n")
        old_amdt_content = old_amdt.amendment_text.split("\n")

        if len(new_amdt_content) == 0 or len(old_amdt_content) == 0:
            logger.warning(f"{new_amdt.num}: has no content")
            return

        dif_html_str = utils.html_diff_lines(
            new_amdt_content,
            old_amdt_content,
            fromdesc=self.xml_amdts.resource_identifier,
            todesc=self.json_amdts.resource_identifier,
        )
        if dif_html_str is not None:
            self.changed_amdts.append(ChangedAmdt(new_amdt.num, dif_html_str))




def main():
    # should we get all the amendments from the API...
    # then try and read the LM XML file
    #

    # read amended details json into a class structure
    # amendmtes_json_path = "amendments_details.json"
    amendmtes_json_path = "amendments_details_Public_Authorities.json"

    with open(amendmtes_json_path) as f:
        amendments_list_json = json.load(f)

    api_amendments: dict[str, Amendment] = {}
    for item in amendments_list_json:

        amendment = Amendment.from_json(item)
        if amendment.num is None:
            logger.warning(
                "Amendment has no marshalledListText"
            )
            continue
        if amendment.num in api_amendments:
            logger.warning("Warning has duplicate marshalledListText")
            continue

        api_amendments[amendment.num] = amendment

    # file_path = "example_files/terminally_ill_adults_rpro_pbc_0212.xml"
    file_path = "example_files/public_authority_rpro_pbc_0227.xml"
    tree = etree.parse(file_path)

    root = tree.getroot()

    xpath = "//xmlns:amendment[@name='hcamnd']/xmlns:amendmentBody[@eId]"

    amendments_xml = root.xpath(xpath, namespaces=NSMAP)

    print(f"No of amendments found in xml: {len(amendments_xml)}")

    # put all the amedments into a structu

    filename = "API_html_diff.html"

    report = Report(root, amendments_list_json)

    report.html_tree.write(
        filename,
        method="html",
        encoding="utf-8",
        doctype="<!DOCTYPE html>",
    )

    webbrowser.open(Path(filename).resolve().as_uri())

    # for i, amendment_xml in enumerate(amendments_xml):

    #     amendment_from_xml = Amendment.from_xml(amendment_xml)

    #     amdt_no = amendment_from_xml.num

    #     if amdt_no not in api_amendments:
    #         print(f"{amdt_no} is missing from the data form the Bills API")
    #         continue

    #     # get text for xml amendments
    #     # clean_amendment_xml = utils.clean_whitespace(amendment_xml)
    #     # xml_amend_text = xp.text_content(clean_amendment_xml)
    #     xml_amend_text = amendment_from_xml.amendment_text

    #     json_amend_text = api_amendments[amdt_no].amendment_text

    #     json_amend_text = f"<div>{json_amend_text}</div>"
    #     json_amend_html = html.fromstring(json_amend_text)
    #     json_amend_text = xp.text_content(json_amend_html)

    #     json_amend_text = normalise_text(json_amend_text)

    #     if xml_amend_text != json_amend_text:
    #         print(f"Text not the same for {amdt_no}")

    #         # pass
    #     if amdt_no == "94":
    #         print(f"{xml_amend_text=}")
    #         print(f"{json_amend_text=}")

    #     # right, we should compare the amdt_json to the amendment XML element
    #     # and see if they match
    """
        # for i, amendment_json in enumerate(amendments_json, start=1):
        #     print(f"Requesting amendment {i} of {len(amendments_json)}")

        #     # get the if for each amendment
        #     amendment_id = amendment_json["amendmentId"]

        #     # get the full amendment json
        #     url = f"https://bills-api.parliament.uk/api/v1/Bills/3774/Stages/19346/Amendments/{amendment_id}"

        #     response = requests.get(url)
        #     amendment_details_json = response.json()
        #     amendments_details_json.append(amendment_details_json)

        # print(f"Total amendments: {len(amendments_details_json)}")
        # json.dump(
        #     amendments_details_json,
        #     open("amendments_details.json", "w", encoding="utf-8"),
        #     ensure_ascii=False,
        #     indent=4,
        # )

        # dict_of_amendments = {}

        # for amendment_json in amendments_json:

        #     marshalledListText = amendment_json.get("marshalledListText", None)
        #     if marshalledListText is None:
        #         continue

        #     if marshalledListText in dict_of_amendments:
        #         print(f"Duplicate: {marshalledListText}")

        #     dict_of_amendments[marshalledListText] = amendment_json
    """





def get_amendment_details_json():

    with open("amendments.json") as f:
        amendments_json = json.load(f)

    # convert amendments_json from a list of dicts to a dict of dicts
    # with marshalledListText as the key

    urls = [
        f"https://bills-api.parliament.uk/api/v1/Bills/3774/Stages/19346/Amendments/{amendment_json['amendmentId']}"
        for amendment_json in amendments_json
    ]

    return progress_bar(map(request_json, urls), len(amendments_json))


def find_duplicate_sponsors(lst: list[Sponsor]) -> list[Sponsor]:
    """
    Find and return a list of duplicate items in the given list.

    This function takes a list of strings and returns a list of items that
    appear more than once in the original list. The returned list contains
    the duplicate items sorted in ascending order.
    """

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
