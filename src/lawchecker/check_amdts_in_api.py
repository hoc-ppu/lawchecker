import argparse
import csv
import json
import re
import sys
import urllib.parse
import webbrowser
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

import requests
from lxml import etree, html
from lxml.etree import QName, _Element, iselement
from lxml.html import HtmlElement

from lawchecker import pp_xml_lxml, templates, utils
from lawchecker import xpath_helpers as xp
from lawchecker.compare_amendment_documents import ChangedAmdt, ChangedNames
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import COMPARE_REPORT_TEMPLATE, NSMAP, NSMAP2, UKL
from lawchecker.stars import BLACK_STAR, NO_STAR, WHITE_STAR, Star

JSON = int | str | float | bool | None | list["JSON"] | dict[str, "JSON"]
JSONObject = dict[str, JSON]
JSONList = list[JSON]
JSONType = JSONObject | JSONList


class ContainerType(StrEnum):
    COMMITTEE_DECISIONS = "Committee Stage Decisions"
    REPORT_DECISIONS = "Report Stage Decisions"
    AMENDMENT_PAPER = "Amendment Paper"
    AMDTS_FROM_API = "Amendments from API"
    UNKNOWN = "Unknown"


def get_container_type(string: str) -> ContainerType:
    string = string.casefold().strip()

    for container_type in ContainerType:
        if container_type.casefold() in string:
            return container_type

    return ContainerType.UNKNOWN


class Decision:

    similar_decisions = [
        ["Agreed", "Agreed To", "Added", "Agreed to on division"],
        ["Withdrawn", "Withdrawn Before Moved", "Withdrawn After Debate"],
        ["No Decision", "Not Called"],
        ["Negatived", "Negatived on division", "Disagreed"],
    ]

    normed_similar_decisions = [
        [item.casefold().replace(" ", "") for item in group] for group in similar_decisions
    ]

    def __init__(self, decision: str):

        self._raw_decision = decision
        self.normed_dec = decision.strip().casefold().replace(" ", "")
        self.decision = self.fix_decision(decision.strip())

        # list of lists with each

    def fix_decision(self, decision: str) -> str:
        """Decisions in the API do not have spaces"""
        return re.sub(r"([a-z])([A-Z])", r"\1 \2", decision)

    def __eq__(self, other: "Decision") -> bool:

        if not isinstance(other, Decision):
            return NotImplemented

        if self.normed_dec == other.normed_dec:
            return True

        # count similar desisions as being equal. This is because the decisions
        # in the API are not the same as the decisions in the XML/proceedings
        # paper. This is for unknown reasons.
        for group in self.normed_similar_decisions:
            if self.normed_dec in group and other.normed_dec in group:
                return True

        return False

    def __bool__(self) -> bool:
        return bool(self.decision)

    def __str__(self):
        return self.decision

    def __repr__(self):
        return f"Decision({self.decision}, {self.normed_dec})"


class InvalidDataError(ValueError):
    """Exception raised for errors in the input JSON data."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def progress_bar(iterable: Iterable, total: int) -> list:

    # also add the progress bar to the webview
    update_gui = False
    active_window = None
    progress_bar_id = ""
    if "webview" in sys.modules:
        import webview
        active_window = webview.active_window()
    if active_window is not None:
        progress_bar_id = active_window.evaluate_js("newProgressBar()")
        logger.info(f"Progress bar id: {progress_bar_id}")
        update_gui = True
    output = []
    count = 0
    bar_len = 50

    sys.stdout.write("\n")

    for item in iterable:
        output.append(item)
        count += 1
        filled_len = int(round(bar_len * count / total))
        percents = round(100.0 * count / total, 1)
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        sys.stdout.write(f"[{bar}] {percents}%\r")
        sys.stdout.flush()

        if update_gui and active_window is not None:
            try:
                active_window.evaluate_js(
                    f"updateProgressBar(\"{progress_bar_id}\", {percents})"
                )
            except Exception as e:
                logger.error(f"Error updating progress bar: {e}")

    sys.stdout.write("\n")

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

        name_match = self.name == other.name
        member_id_match = self.member_id == other.member_id
        is_lead_match = self.is_lead == other.is_lead
        sort_order_match = self.sort_order == other.sort_order

        return (
            name_match and member_id_match and is_lead_match and sort_order_match
        )

    def __lt__(self, other: "Sponsor") -> bool:
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @classmethod
    def from_json(cls, sponsor: dict[str, Any]) -> "Sponsor":

        # TODO: make this more similar to the XML version

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
        decision: Decision,
        sponsors: list[Sponsor],
        parent: "AmdtContainer | None" = None,
        star: Star = NO_STAR,
        id: str = "",
    ):

        self.amendment_text = amendment_text
        self.explanatory_text = explanatory_text
        self.num: str = amendment_number
        self.decision: Decision = decision
        self.sponsors: list[Sponsor] = sponsors
        self.parent: "AmdtContainer | None" = parent
        self.star = star
        self.id = id

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
        amendment_text = "<div>" + "\n".join(amendment_text_gen) + "</div>"
        html_element = html.fromstring(amendment_text)
        # add space after any span with a class of "sub-para-num" this will be important later
        for span in html_element.xpath(".//span[@class='sub-para-num']"):
            if span.tail:
                span.tail = f" {span.tail}"
            else:
                span.tail = " "
        amendment_text = utils.normalise_text(
            xp.text_content(utils.clean_whitespace(html_element))
        )

        explanatory_text = amendment_json.get("explanatoryText", "")

        amendmet_number: str = amendment_json.get(
            "marshalledListText", ""
        )  # amendment_no
        decision: Decision = Decision(amendment_json.get("decision", ""))
        # self.decision_explanation: str = amendment_json.get("decisionExplanation", "")
        sponsors = [
            Sponsor.from_json(item) for item in amendment_json.get("sponsors", [])
        ]

        _star: str | None = amendment_json.get("statusIndicator", None)
        if _star is None:
            star: Star = Star.none()
        else:
            star = Star(_star)

        _id = amendment_json.get("amendmentId", "")

        return cls(
            amendment_text, explanatory_text, amendmet_number, decision, sponsors, parent, star, _id
        )

    @classmethod
    def from_xml(cls, amendment_xml: _Element, parent: "AmdtContainer | None" = None) -> "Amendment":
        # assume amendment_xml is an amendmentBody element

        # get the decision
        decision_block = amendment_xml.xpath(
            './/xmlns:block[@name="decision"]', namespaces=NSMAP
        )
        decision = ""
        if len(decision_block) > 0:
            decision = utils.normalise_text(xp.text_content(decision_block[0]))
        decision = Decision(decision)

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

        add_quotes_to_quoted_elements(amendment_content)

        amendment_text = utils.normalise_text(
            xp.text_content(utils.clean_whitespace(amendment_content))
        )

        star = Star(amendment_xml.get(QName(UKL, "statusIndicator"), default=""))

        _id = amendment_xml.xpath(".//*/@GUID[1]", namespaces=NSMAP)[0]
        # print(f"ID: {_id}")


        return cls(amendment_text, explanatory_text, amdt_no, decision, sponsors, parent, star, _id)


def normalise_amendments_xml(amendment_xml: _Element) -> _Element:
    raise NotImplementedError


def add_quotes_to_quoted_elements(amendment_element: _Element) -> None:

    """Element is modified in place"""

    # get the text
    # if there is a quoted structure there could be strangeness with quotes
    quoted_elements: list[_Element] = amendment_element.xpath(
        ".//xmlns:*[@ukl:endQuote or @ukl:startQuote or @endQuote or @startQuote]", namespaces=NSMAP
    )
    # print(f"Quoted Elements: {len(quoted_elements)}")
    for qs in quoted_elements:
        tag = QName(qs).localname
        if tag == "def":
            print(f"Def: {qs.text}")
            # print(qs.attrib)
        if qs.get("startQuote") == "“" or qs.get(f"{{{UKL}}}startQuote") == "“":

            if qs.text:
                qs.text = f'“{qs.text}'

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
        self.container_type: ContainerType = container_type
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
            self.container_type = get_container_type(list_type_text)
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
                logger.warning(f"{self.container_type}: Duplicate amendment number: {amendment.num}")
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

        # here we will put all amendments that arn't correctly in the API
        # including missing amendments, amendments with incorrect content,
        # amendments with incorrect names, incorrect decisions etc.
        # do we need this, could we not just add the other lists together?
        self.problem_amdts: list[ChangedAmdt] = []

        self.incorrect_amdt_in_api: list[ChangedAmdt] = []
        self.incorrect_decisions: list[str] = []
        self.correct_decisions: list[str] = []

        self.missing_api_amdts: list[str] = []

        self.no_name_changes: list[str] = []
        self.name_changes: list[ChangedNames] = []
        # self.duplicate_names: list[str] = []
        self.name_changes_in_context: list[ChangedAmdt] = []

        self.correct_stars: list[str] = []
        self.incorrect_stars: list[str] = []

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
        self.check_stars_in_api(self.xml_amdts, self.json_amdts)

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
            self.diff_decision(xml_amdt, json_amend)


    def make_html(self):
        """
        Build up HTML document with various automated checks on amendments
        """

        try:
            # change the title
            self.html_root.find('.//title').text = "Check Amendments"  # type: ignore
            self.html_root.find('.//h1').text = "Check Amendments on Bills.parliament.uk"  # type: ignore
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
                self.render_stars(),
                self.render_changed_amdts(),
                self.render_decisions(),
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
            ("List Type", self.xml_amdts.container_type)
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
        if self.missing_api_amdts:
            removed_content = (
                f"Missing content: <strong>{len(self.missing_api_amdts)}</strong><br />"
                f"{' '.join(self.missing_api_amdts)}"
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

        name_changes = templates.Table(("Ref", "Names missing from API", "Names in API but not in XML", "Totals"))

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

        no_name_changes: HtmlElement | None = None

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
                    " have different names in the API: </p>\n"
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

        card = templates.Card("Check Names")
        card.secondary_info.extend(
            (
                name_changes_table,
                names_change_context_section.html,
            )
        )
        if no_name_changes is not None:
            card.tertiary_info.append(no_name_changes)

        return card.html

    def render_stars(self) -> HtmlElement:
        # -------------------- Star check section -------------------- #
        # build up text content
        correct_stars: HtmlElement | None = None
        if self.correct_stars:

            sec = (templates.SmallCollapsableSection(
                f"<span><strong>{len(self.correct_stars)}</strong>"
                f" amendments have correct stars: "
                '<small class="text-muted"> [show]</small></span>'
            ))
            sec.collapsible.text = f"{', '.join(self.correct_stars)}"
            correct_stars = sec.html

        incorrect_stars = (
            "All amendments have correct stars"
        )
        if self.incorrect_stars:
            incorrect_stars = (
                f'<strong class="red">{len(self.incorrect_stars)} amendments'
                f" have incorrect stars:</strong>  {', '.join(self.incorrect_stars)}"
            )

        card = templates.Card("Star Check")
        card.secondary_info.append(html.fromstring(f"<p>{incorrect_stars}</p>"))
        if correct_stars is not None:
            card.tertiary_info.append(correct_stars)

        return card.html


    def render_changed_amdts(self) -> HtmlElement:
        # -------------------- Changed Amendments -------------------- #
        # build up text content
        changed_amdts = (
            "<p>Amendments in the API match those in the XML 😀</p>"
        )
        if self.incorrect_amdt_in_api:
            changed_amdts = (
                f'<p><strong class="red">{len(self.incorrect_amdt_in_api)}</strong>'
                " amendments have incorrect content in the API: </p>\n"
            )
            for item in self.incorrect_amdt_in_api:
                changed_amdts += f"<p class='h5'>{item.num}:</p>\n{item.html_diff}\n"

        card = templates.Card("Changed amendments")
        card.secondary_info.extend(
            html.fragments_fromstring(changed_amdts, no_leading_text=True)
        )

        return card.html

    def render_no_decision_check(self) -> HtmlElement:

        card = templates.Card("Decision Check")
        card.secondary_info.append(
            html.fromstring(
                "<p>The XML file does not appear to be a proceedings"
                " paper so no decisions have been checked.</p>"
            )
        )
        return card.html


    def render_decisions(self) -> HtmlElement:

        # -------------------- Decision check section -------------------- #

        is_report_decisions = self.xml_amdts.container_type == ContainerType.REPORT_DECISIONS
        is_committee_decisions = self.xml_amdts.container_type == ContainerType.COMMITTEE_DECISIONS

        if is_report_decisions or is_committee_decisions:
            return self.render_no_decision_check()

        # build up text content
        correct_decisions: HtmlElement | None = None

        if self.correct_decisions:
            sec = (templates.SmallCollapsableSection(
                f"<span><strong>{len(self.correct_decisions)}</strong>"
                f" amendments in the API have decisions which match the"
                " decision in the provided XML file: "
                '<small class="text-muted"> [show]</small></span>'
            ))
            sec.collapsible.text = f"{', '.join(self.correct_decisions)}"
            correct_decisions = sec.html

        if self.incorrect_decisions:
            incorrect_decisions = (
                f'<p><strong class="red">{len(self.incorrect_decisions)}</strong>'
                " amendments in the API have decisions which do not match the decision in the provided XML file: </p>\n"
            )
            incorrect_decisions += f"<p>{'<br/>'.join(self.incorrect_decisions)}</p>"
        else:
            incorrect_decisions = (
                "<p>Every decision (on all amendments) in the API matches the decision in the XML. 😀</p>"
            )

        note = '<p class="small"><strong>Note:</strong> For unknown reasons, decisions recorded in a the proceedings paper do not map onto the decisions in the API (and by extension, the amendments section of bills.parliament.uk). For the purposes of this check the following groups of decisions are considered to be the same:</p>'
        list_items = [f"<li>{', '.join(l)}</li>" for l in Decision.similar_decisions]
        note += f"<ul class='small'>{''.join(list_items)}</ul>"

        card = templates.Card("Decision Check")
        card.secondary_info.append(html.fromstring(f"<div>{note + incorrect_decisions}</div>"))

        if correct_decisions is not None:
            card.tertiary_info.append(correct_decisions)

        return card.html

    def check_stars_in_api(
        self,
        xml_amdts: AmdtContainer,
        api_amdts: AmdtContainer,
    ):

        """
        Check that amendments that apprear in both the XML and the API have the
        correct star in the API. If the amendment is not in the XML then we
        don't need to check the star.
        """

        for key, xml_amdt in xml_amdts.items():
            if key not in api_amdts:
                continue
            api_amdt = api_amdts[key]

            if api_amdt.star == xml_amdt.star:
                self.correct_stars.append(f"{api_amdt.num} ({api_amdt.star})")
            else:
                self.incorrect_stars.append(
                    f"{api_amdt.num} has {api_amdt.star} ({xml_amdt.star} expected)"
                )


    def added_and_removed_amdts(self, old_doc: "AmdtContainer", new_doc: "AmdtContainer"):

        """Find the amendment numbers missing from the API"""

        self.missing_api_amdts = list(old_doc.amdt_set.difference(new_doc.amdt_set))

        # we don't need amendments in the API but not in the document
        # self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

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

        # sometimes the line breaks are different due to ref elements etc.
        # so first we will compare the text content normalised and with the
        # line breaks removed
        new_amdt_content_no_lines = utils.normalise_text(" ".join(new_amdt_content))
        old_amdt_content_no_lines = utils.normalise_text(" ".join(old_amdt_content))

        # if new_amdt.num == "59":
        #     print(new_amdt_content_no_lines)
        #     print(old_amdt_content_no_lines)

        if new_amdt_content_no_lines == old_amdt_content_no_lines:
            logger.info(f"{new_amdt.num}: content the same when line breaks removed.")
            return

        dif_html_str = utils.html_diff_lines(
            new_amdt_content,
            old_amdt_content,
            fromdesc=self.xml_amdts.resource_identifier,
            todesc=self.json_amdts.resource_identifier,
        )
        if dif_html_str is not None:
            self.incorrect_amdt_in_api.append(ChangedAmdt(new_amdt.num, dif_html_str))

    def diff_decision(self, xml_amdt: Amendment, api_amdt: Amendment):

        """
        Check that the decision in the API matches the decision in the XML.
        """

        xml_decision = xml_amdt.decision
        api_decision = api_amdt.decision

        if not xml_decision:
            # no decision in the XML so no point comparing
            return

        if xml_decision == api_decision:
            # I don't think we need to strip here
            self.correct_decisions.append(xml_amdt.num)
        else:
            self.incorrect_decisions.append(f"{xml_amdt.num} (API: {api_decision}, XML: {xml_decision})")

    def create_csv(self):

        # build up the text strings
        bill_title_text = self.xml_amdts.meta_bill_title
        missing_amendment_text = ""
        missing_amendment_guids = ""

        if all(
            [len(i) == 0 for i in (
                self.missing_api_amdts, self.incorrect_amdt_in_api, self.name_changes, self.incorrect_stars
            )]
        ):
            logger.warning("No problems were found so no CSV file will be created.")
            return

        logger.warning(
            f"{len(self.missing_api_amdts)} Missing amendments."
            f" {len(self.incorrect_amdt_in_api)} incorrect amendments."
            f" {len(self.name_changes)} amendment have incorrect names."
            f" {len(self.incorrect_stars)} amendments have incorrect stars."
        )

        if len(self.missing_api_amdts) > 0:
            missing_amendment_guids = missing_amendment_text = "Missing Amendments:\n"

        logger.info("here 1")

        for item in self.missing_api_amdts:
            missing_amendment_text += f"{item}\n"
            missing_amendment_guids += f"{self.xml_amdts[item].id}\n"

        logger.info("here 2")

        incorrect_amendments_text = ""
        incorrect_amendment_guids = ""
        if len(self.incorrect_amdt_in_api) > 0:
            incorrect_amendments_text = "Amendments with incorrect content:\n"
            incorrect_amendment_guids = "Amendments with incorrect content:\n"
        for item in self.incorrect_amdt_in_api:
            incorrect_amendments_text += f"{item.num}\n"
            incorrect_amendment_guids += f"{self.xml_amdts[item.num].id}\n"

        logger.info("here 3")

        incorrect_names = ""
        incorrect_names_guids = ""
        if len(self.name_changes) > 0:
            incorrect_names = "Amendments with incorrect names:\n"
            incorrect_names_guids = "Amendments with incorrect names:\n"
        for item in self.name_changes:
            incorrect_names += f"{item.num}\n"
            incorrect_names_guids += f"{self.xml_amdts[item.num].id}\n"

        logger.info("here 4")

        incorrect_stars = ""
        incorrect_stars_guids = ""
        if len(self.incorrect_stars) > 0:
            incorrect_stars = "Amendments with incorrect stars:\n"
            incorrect_stars_guids = "Amendments with incorrect stars:\n"
        for item in self.incorrect_stars:
            incorrect_stars += f"{item}\n"
            try:
                amdt_num = item.split(" has ")[0]
                incorrect_stars_guids += f"{self.xml_amdts[amdt_num].id}\n"
            except Exception as e:
                logger.error(f"Error getting GUID for {item}: {e}")

        logger.info("here 5")

        problem_amendment_numbers = missing_amendment_text + incorrect_amendments_text + incorrect_names + incorrect_stars
        problem_amendment_guids = missing_amendment_guids + incorrect_amendment_guids + incorrect_names_guids + incorrect_stars_guids

        logger.warning("here")

        file_name = Path("test_test.csv").resolve()

        with open(file_name, 'w', newline='') as file:
            # Step 3: Create a csv.writer object
            writer = csv.writer(file)

            # Step 4: Write a header row
            writer.writerow(['Bill', 'Amendment Numbers', 'GUIDs', 'Description'])

            # Step 4: Write a data row
            writer.writerow([bill_title_text, problem_amendment_numbers, problem_amendment_guids])

        logger.warning(f"CSV file created: {file_name}")


def also_query_bills_api(amend_xml_path: Path) -> JSONList | None:
    """
    Query the API for the bill XML files related to the amendment XML file.
    """

    if not amend_xml_path:
        logger.error("No amendment XML file selected.")
        return

    amend_xml = pp_xml_lxml.load_xml(str(amend_xml_path))

    if not amend_xml:
        logger.error(f"Amendment XML file is not valid XML: {amend_xml_path}")
        return

    # find the bill title from the amendment XML
    amdt_xml_root = amend_xml.getroot()
    try:
        bill_title = amdt_xml_root.xpath('//xmlns:TLCConcept[@eId="varBillTitle"]/@showAs', namespaces=NSMAP)[0]
        logger.info(f"Bill title found in XML: {bill_title}")

    except Exception as e:
        logger.error("Could not find bill title in amendment XML. Can't query API.")
        logger.error(repr(e))
        return
    # TODO: remember to normalise the bill title
    try:
        # url encode the title
        bill_title = urllib.parse.quote(bill_title)
        url = f"https://bills-api.parliament.uk/api/v1/Bills?SearchTerm={bill_title}&SortOrder=DateUpdatedDescending"
        logger.info(f"Querying: {url}")
        response = requests.get(url)
    except Exception:
        logger.error("Error querying the API")
        return
    if response.status_code != 200:
        logger.error("Error querying the API")
        return

    response_json: JSONObject = response.json()

    file_name = "amendments_details.json"
    json.dump(response_json, open(file_name, "w"), ensure_ascii=False, indent=2)
    logger.info(Path(file_name).resolve())

    bills: list = response_json.get("items", [])

    if not bills:
        logger.error(f"No bills found in the API with the title \"{bill_title}\"")
        return
    if len(bills) > 1:
        logger.warning(
            f"{len(bills)} bills found in the API with the query \"{bill_title}\"."
            " Using the first bill found."
        )

    bill_json = bills[0]

    # try to get the stage from the xml
    stage: str | None = None
    try:
        # block = amdt_xml_root.xpath('//*[local-name()="block"][@name="stage"]')
        stage = xp.text_content(amdt_xml_root.xpath('//xmlns:block[@name="stage"]/xmlns:docStage', namespaces=NSMAP)[0])
    except Exception as e:
        logger.warning("Could not find stage in amendment XML. Can't query API.")
        logger.warning(repr(e))
        return

    # TODO: fix this
    api_stage = bill_json.get("currentStage", {}).get("description", "")

    bill_id: int | None = bill_json.get("billId", None)
    stage_id: int | None = bill_json.get("currentStage", {}).get("id", None)

    if stage.casefold().strip() != api_stage.casefold().strip():
        logger.info(
            f"Stage in amendment XML ({stage}) does not match current stage in API ({api_stage})."
        )
        # look thorugh all other stages to get the correct one
        try:
            url = f"https://bills-api.parliament.uk/api/v1/Bills/{bill_json['billId']}/Stages"
            response = requests.get(url)
            response_json = response.json()
            stages = response_json.get("items", [])
            for item in stages:
                description = item.get("description", "")
                if description.casefold().strip() == stage.casefold().strip():

                    api_stage = description
                    stage_id = item.get("id", None)
                    logger.info(f"Stage found in API: {api_stage}. Stage ID: {stage_id}")
                    break
        except Exception as e:
            logger.error("Error getting stages from API.")
            logger.error(repr(e))


    logger.notice(f"Bill ID: {bill_id} Stage ID: {stage_id}")

    if not all([bill_id, stage_id]):
        logger.error("Could not get bill ID or stage ID from the API.")
        return

    return get_amendments_json(bill_id, stage_id)


def get_amendments_json(bill_id, stage_id: int) -> list[JSONType]:

    json_summary_amendments = get_amendments_summary_json(bill_id, stage_id)

    amendment_ids = [amendment.get("amendmentId") for amendment in json_summary_amendments]

    def _request_data(
        amendment_id: str,
    ) -> requests.Response:

        """Query the API."""

        url = f"https://bills-api.parliament.uk/api/v1/Bills/{bill_id}/Stages/{stage_id}/Amendments/{amendment_id}"

        return requests.get(url)

    with ThreadPoolExecutor(max_workers=8) as pool:

        # create a progress bar and return a list
        responses = progress_bar(
            pool.map(
                lambda amendment_id: _request_data(amendment_id),
                amendment_ids,
            ),
            len(amendment_ids),
        )
        print()  # newline after progress bar

    json_list: list[JSONType] = [response.json() for response in responses]

    json.dump(json_list, open("amendments_details.json", "w"), indent=2)
    logger.info("Amendments details saved to file: amendments_details.json")

    return json_list


def get_amendments_summary_json(bill_id: int, stage_id: int) -> list[JSONObject]:

    i = 0
    json_amendments = []
    while True:
        skip = i * 20
        url = f"https://bills-api.parliament.uk/api/v1/Bills/{bill_id}/Stages/{stage_id}/Amendments?skip={skip}"

        response = requests.get(url)
        response_json = response.json()
        items = response_json["items"]
        if len(items) == 0:
            break
        json_amendments += items

        i += 1

    return json_amendments


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


def main():

    parser = argparse.ArgumentParser(
        description="Compare amendments between an XML file and the API. If no JSON file is provided, the API will be queried automatically."
    )
    parser.add_argument("xml_file", type=argparse.FileType('rb'), help="XML amendment or proceedings file path")
    parser.add_argument(
        "--json",
        type=argparse.FileType('r'),
        metavar="json_file",
        default=None,
        help="Existing JSON file with amendments details"
    )
    args = parser.parse_args()

    if args.json:
        amendments_list_json = json.load(args.json)
    else:
        amendments_list_json = also_query_bills_api(Path(args.xml_file.name))

    if not amendments_list_json:
        logger.error("No amendments found from JSON file or API. Exiting.")
        return 1

    tree = etree.parse(args.xml_file)
    root = tree.getroot()

    xpath = "//xmlns:amendment[@name='hcamnd']/xmlns:amendmentBody[@eId]"

    amendments_xml = root.xpath(xpath, namespaces=NSMAP)

    logger.info(f"No. of amendments found in xml: {len(amendments_xml)}")

    filename = "API_html_diff.html"

    report = Report(root, amendments_list_json)

    report.html_tree.write(
        filename,
        method="html",
        encoding="utf-8",
        doctype="<!DOCTYPE html>",
    )

    webbrowser.open(Path(filename).resolve().as_uri())


if __name__ == "__main__":
    main()
