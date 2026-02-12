import argparse
import asyncio
import csv
import json
import logging
import math
import os
import re
import sys
import urllib.parse
import webbrowser
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, NamedTuple

from lxml import etree, html
from lxml.etree import QName, _Element, iselement
from lxml.html import HtmlElement

from lawchecker import (
    __version__,
    bills_api,
    common,
    lawchecker_logger,
    pp_xml_lxml,
    templates,
    utils,
)
from lawchecker import xpath_helpers as xp
from lawchecker.compare_bill_numbering import clean as clean_filename
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import (
    AMENDMENT_DETAILS_URL_TEMPLATE,
    AMENDMENTS_URL_TEMPLATE,
    COMPARE_REPORT_TEMPLATE,
    NSMAP,
    NSMAP2,
    PARSER,
    UKL,
)
from lawchecker.stars import NO_STAR, Star

JSON = int | str | float | bool | None | list['JSON'] | dict[str, 'JSON']
JSONObject = dict[str, JSON]
JSONList = list[JSON]
JSONType = JSONObject | JSONList


# Shared requests.Session with retries/timeouts to reduce transient failures
DEFAULT_TIMEOUT = 10  # seconds

# SESSION = requests.Session()
# RETRY_STRATEGY = Retry(
#     total=3,
#     backoff_factor=0.5,
#     status_forcelist=[429, 500, 502, 503, 504],
#     allowed_methods=['HEAD', 'GET', 'OPTIONS'],
# )
# ADAPTER = HTTPAdapter(max_retries=RETRY_STRATEGY)
# SESSION.mount('https://', ADAPTER)
# SESSION.mount('http://', ADAPTER)
# # prevent socket reuse which can trigger EOF errors from some servers/proxies
# SESSION.headers.update(
#     {
#         'Connection': 'close',
#         'User-Agent': 'LawChecker/1.0',
#     }
# )


class ContainerType(StrEnum):
    COMMITTEE_DECISIONS = 'Committee Stage Decisions'
    REPORT_DECISIONS = 'Report Stage Decisions'
    AMENDMENT_PAPER = 'Amendment Paper'
    AMDTS_FROM_API = 'Amendments from API'
    UNKNOWN = 'Unknown'


def get_container_type(string: str) -> ContainerType:
    string = string.casefold().strip()

    for container_type in ContainerType:
        if container_type.casefold() in string:
            return container_type

    return ContainerType.UNKNOWN


#
class ChangedNames(NamedTuple):
    # note different to compare_amendment_documents.ChangedNames
    num: str  # do we need this?
    added: list[str]
    removed: list[str]
    ref: 'AmdtRef'


@dataclass
class ChangedAmdt:
    # note different to compare_amendment_documents.ChangedAmdt
    ref: 'AmdtRef'
    html_diff: str

    @property
    def num(self) -> str:
        return self.ref.short_ref


@dataclass
class ReportMetadata:
    """Optional metadata to include in the HTML report intro section.

    This class allows callers (e.g., monster) to pass additional context
    about the report generation, such as LawMaker project info and API
    stage matching details.
    """

    lm_project_title: str | None = None
    lm_stage: str | None = None
    api_stage_description: str | None = None
    api_stage_id: int | None = None
    api_bill_id: int | None = None
    official_list_label: str | None = None
    generation_timestamp: datetime | None = None


class Decision:
    similar_decisions = [
        ['Agreed', 'Agreed To', 'Added', 'Agreed to on division'],
        ['Withdrawn', 'Withdrawn Before Moved', 'Withdrawn After Debate'],
        ['No Decision', 'Not Called'],
        ['Negatived', 'Negatived on division', 'Disagreed'],
    ]

    normed_similar_decisions = [
        [item.casefold().replace(' ', '') for item in group]
        for group in similar_decisions
    ]

    def __init__(self, decision: str):
        self._raw_decision = decision
        self.normed_dec = decision.strip().casefold().replace(' ', '')
        self.decision = self.fix_decision(decision.strip())

        # list of lists with each

    def fix_decision(self, decision: str) -> str:
        """Decisions in the API do not have spaces"""
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', decision)

    def __eq__(self, other: 'Decision') -> bool:
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
        return f'Decision({self.decision}, {self.normed_dec})'


class InvalidDataError(ValueError):
    """Exception raised for errors in the input JSON data."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AmdtRef:
    """Reference to an amendment by number and dnum"""

    def __init__(self, num: str, dnum: str):
        # could num just be the empty string?
        if not num and not dnum:
            logger.warning(f'AmdtRef(num={num}, dnum={dnum})')
            raise ValueError('Both num and dnum cannot be empty')
        if not dnum:
            logger.info(f'Creating AmdtRef with empty dnum for num: {num}')
            dnum = ''
        if not num:
            # this happens a lot in Lords running lists
            num = ''

        self.num: str = num
        self.dnum: str = dnum

    def __str__(self) -> str:
        if self.num:
            return f'{self.num} ({self.dnum})'
        return self.dnum

    def __repr__(self) -> str:
        return f'AmdtRef(num={self.num}, dnum={self.dnum})'

    @property
    def short_ref(self) -> str:
        if self.num:
            return self.num
        return self.dnum

    @property
    def long_ref(self) -> str:
        # return f'{self.num} ({self.dnum})' if self.num else self.dnum
        return f'{self.num} ({self.dnum})'

    def __hash__(self) -> int:
        return hash((self.num, self.dnum))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AmdtRef):
            return NotImplemented
        return self.num == other.num and self.dnum == other.dnum


def progress_bar(iterable: Iterable, total: int) -> list:
    # also add the progress bar to the webview
    active_window = common.RunTimeEnv.webview_window
    progress_bar_id = ''

    if active_window is not None:
        progress_bar_id = active_window.evaluate_js('newProgressBar()')
        logger.info(f'Progress bar id: {progress_bar_id}')
    output = []
    count = 0
    bar_len = 50

    sys.stdout.write('\r')

    last_percent = 0
    for item in iterable:
        output.append(item)
        count += 1
        filled_len = int(round(bar_len * count / total))
        percents = round(100.0 * count / total)

        if percents == last_percent:
            continue
        last_percent = percents

        bar = '#' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write(f'[{bar}] {percents}%\r')
        sys.stdout.flush()

        if active_window is None:
            continue

        # consider window.evaluate_js which raises exceptions on js errors
        active_window.run_js(f'updateProgressBar("{progress_bar_id}", {percents})')

    sys.stdout.write('\n')

    return output


async def async_progress_bar(
    tasks: Iterable,
    error_prefix: str = 'Task failed',
    bar_len: int = 50,
    log_level: int = logging.ERROR,
) -> list:
    """Execute async tasks with a console progress bar.

    Args:
        tasks: Iterable of async tasks/coroutines to execute.
        error_prefix: Prefix for error log messages when a task fails.
        bar_len: Length of the progress bar in characters.
        log_level: Logging level for error messages (default: logging.ERROR).

    Returns:
        List of results, with exceptions for failed tasks.
    """

    # also add the progress bar to the webview
    active_window = common.RunTimeEnv.webview_window
    progress_bar_id = ''

    if active_window is not None:
        progress_bar_id = active_window.evaluate_js('newProgressBar()')
        logger.info(f'Progress bar id: {progress_bar_id}')

    tasks_list = list(tasks)
    responses = []
    total = len(tasks_list)
    count = 0

    print('\n', end='', flush=True)
    last_percents: int = -1
    for coro in asyncio.as_completed(tasks_list):
        try:
            result = await coro
            responses.append(result)
        except Exception as e:
            logger.log(log_level, f'{error_prefix}: {repr(e)}')
            responses.append(e)

        count += 1
        filled_len = int(round(bar_len * count / total))
        percents = int(round(100.0 * count / total))
        if percents != last_percents:
            last_percents = percents
            bar = '#' * filled_len + '-' * (bar_len - filled_len)
            sys.stdout.write(f'[{bar}] {percents}%\r')
            sys.stdout.flush()

        if active_window is None:
            continue

        # consider window.evaluate_js which raises exceptions on js errors
        active_window.run_js(f'updateProgressBar("{progress_bar_id}", {percents})')

    sys.stdout.write('\n')

    return responses


# def get_json_sync(url: str) -> JSONObject:
#     try:
#         response = SESSION.get(url, timeout=DEFAULT_TIMEOUT)
#         response.raise_for_status()
#         return response.json()
#     except RequestException as e:
#         logger.error(f'HTTP error fetching JSON from {url}: {e}')
#         raise


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

    def __repr__(self) -> str:
        return (
            f'Sponsor(name={self.name}, member_id={self.member_id}, '
            f'is_lead={self.is_lead}, sort_order={self.sort_order})'
        )

    def __eq__(self, other: 'Sponsor') -> bool:
        """Check if two sponsors are the same"""

        # Here we will not actually compare the name text, as sometimes someone
        # can be for example 'Secretary Wes Streeting' and 'Wes Streeting'
        if not isinstance(other, Sponsor):
            return NotImplemented

        # name_match = self.name == other.name
        member_id_match = self.member_id == other.member_id
        # is_lead_match = self.is_lead == other.is_lead

        # dont need to mind about sort order
        # sort_order_match = self.sort_order == other.sort_order

        # return name_match and member_id_match and is_lead_match and sort_order_match
        return member_id_match  # and is_lead_match  # and sort_order_match

    def __lt__(self, other: 'Sponsor') -> bool:
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @classmethod
    def from_json(cls, sponsor: dict[str, Any]) -> 'Sponsor':
        # TODO: make this more similar to the XML version

        name: str | None = sponsor.get('name', None)
        member_id: int | None = sponsor.get('memberId', None)
        is_lead: bool | None = sponsor.get('isLead', None)
        sort_order: int | None = sponsor.get('sortOrder', None)

        if any((i is None for i in (name, member_id, is_lead, sort_order))):
            raise InvalidDataError(
                'Error: Sponsor JSON data is invalid or missing required fields'
            )

        return cls(name, member_id, is_lead, sort_order)  # type: ignore

    @classmethod
    def from_supporters_xml(cls, supporters: list[_Element]) -> list['Sponsor']:
        # from <block name="supporters">
        sponsors: list[Sponsor] = []

        for i, element in enumerate(supporters, start=1):
            # is_lead = i == 1
            tag = QName(element).localname
            if tag not in ('docProponent', 'docIntroducer'):
                logger.info(f'Unexpected tag {tag} in supporters block')
                continue

            is_lead = tag == 'docIntroducer'

            refers_to = element.get('refersTo')
            if not refers_to:
                logger.error('docProponent element has no refersTo attribute')
                continue
            try:
                mnis_id = int(refers_to.split('-')[-1])
            except (IndexError, ValueError):
                logger.error(
                    'docProponent refersTo attribute is not in the expected format'
                )
                continue
            if not element.text:
                logger.error('docProponent element has no text')
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
        parent: 'AmdtContainer | None' = None,
        star: Star = NO_STAR,
        id: str = '',
        dnum: str = '',
    ):
        self.amendment_text = amendment_text
        self.explanatory_text = explanatory_text
        self.num: str = utils.clean_amendment_number(amendment_number)
        self.decision: Decision = decision
        self.sponsors: list[Sponsor] = sponsors
        self.parent: 'AmdtContainer | None' = parent
        self.star = star
        self.id = id
        self.dnum = dnum.strip().casefold()
        self.key = AmdtRef(num=self.num, dnum=self.dnum)

        # we might need to come up with an amendment id that is the same for both
        # the API and the XML... in particular a problem with amendments to amendments

    def __eq__(self, other: 'Amendment') -> bool:
        if not isinstance(other, Amendment):
            return NotImplemented

        self_num_cleaned = self.num.replace('(', '').replace(')', '')
        other_num_cleaned = other.num.replace('(', '').replace(')', '')

        return (
            self.amendment_text == other.amendment_text
            and self.explanatory_text == other.explanatory_text
            and self_num_cleaned == other_num_cleaned
            and self.decision == other.decision
            and self.sponsors == other.sponsors
        )

    @classmethod
    def from_json(
        cls, amendment_json: dict, parent: 'AmdtContainer | None' = None
    ) -> 'Amendment':
        amendment_text_gen = (
            f'{t.get("hangingIndentation", "") or ""} {t.get("text", "")}'.strip()
            for t in amendment_json.get('amendmentLines', [])
        )
        amendment_text = '<div>' + '\n'.join(amendment_text_gen) + '</div>'
        html_element = html.fromstring(amendment_text)

        # add space after any span with a class of
        # "sub-para-num" this will be important later
        for span in html_element.xpath(".//span[@class='sub-para-num']"):
            if span.tail:
                span.tail = f' {span.tail}'
            else:
                span.tail = ' '
        # amendment_text = utils.normalise_text(
        #     xp.text_content(utils.clean_json_html_amdt(html_element))
        # )
        amendment_text = utils.normalise_text(xp.text_content(html_element))

        explanatory_text_html = amendment_json.get('explanatoryText', '')
        if explanatory_text_html:
            explanatory_text = utils.normalise_text(
                xp.text_content(html.fromstring(f'<div>{explanatory_text_html}</div>'))
            )
        else:
            explanatory_text = ''

        amendmet_number: str = amendment_json.get(
            'marshalledListText', ''
        )  # amendment_no
        decision: Decision = Decision(amendment_json.get('decision', ''))
        # self.decision_explanation: str = amendment_json.get("decisionExplanation", "")
        sponsors = [
            Sponsor.from_json(item) for item in amendment_json.get('sponsors', [])
        ]

        _star: str | None = amendment_json.get('statusIndicator', None)
        if _star is None:
            star: Star = Star.none()
        else:
            star = Star(_star)

        _id = amendment_json.get('amendmentId', '')

        dnum = amendment_json.get('dNum', '')

        return cls(
            amendment_text,
            explanatory_text,
            amendmet_number,
            decision,
            sponsors,
            parent,
            star,
            _id,
            dnum,
        )

    @classmethod
    def from_xml(
        cls, amendment_xml: _Element, parent: 'AmdtContainer | None' = None
    ) -> 'Amendment':
        # assume amendment_xml is an amendmentBody element

        # default dnum to empty string
        dnum = ''

        # get the decision
        decision_block = amendment_xml.xpath(
            './/xmlns:block[@name="decision"]', namespaces=NSMAP
        )
        decision = ''
        if len(decision_block) > 0:
            decision = utils.normalise_text(xp.text_content(decision_block[0]))
        decision = Decision(decision)

        #  get the amendment number
        # try:
        #     e_id = amendment_xml.xpath(
        #         'xmlns:amendment/xmlns:amendmentBody/@eId', namespaces=NSMAP
        #     )[0]
        #     amdt_no = e_id.split('_')[-1]
        # except Exception:
        #     print('Warning no amendment number found')
        #     amdt_no = ''

        # get the sponsors
        # proposer = xp.get_doc_introducer(amendment_xml)
        # supporters = xp.get_doc_proponents(amendment_xml)
        sponsors = Sponsor.from_supporters_xml(xp.get_name_elements_2(amendment_xml))

        # get the explanatory text
        explanatory_text_ps = amendment_xml.xpath(
            './/xmlns:amendmentJustification/xmlns:blockContainer[@class="explanatoryStatement"]//xmlns:p',
            namespaces=NSMAP,
        )
        explanatory_text = '\n'.join(xp.text_content(p) for p in explanatory_text_ps)

        # get amendment text
        try:
            amendment_content = xp.get_amdt_content_2(amendment_xml)[0]
        except IndexError:
            logger.error('No amendment content found')
            raise

        try:
            dnum = amendment_content.xpath('.//xmlns:num/@ukl:dnum', namespaces=NSMAP)[
                0
            ]
            # raise a TypeError if dnum is not a string
            if not isinstance(dnum, str):
                raise InvalidDataError(
                    f'dNum attribute is not a string, got {type(dnum).__name__}'
                    f': {repr(dnum)}'
                )
            if not dnum.strip():
                raise InvalidDataError('dNum attribute is empty or whitespace only')
            # logger.info(f'dNum: {dnum}')

        except IndexError:
            logger.warning('No dNum attribute found in amendment content')
        except Exception as e:
            logger.warning(f'Error getting dNum: {repr(e)}')

        amdt_no = ''
        try:
            amendment_num = amendment_content.find(
                './/xmlns:num[@ukl:dnum]', namespaces=NSMAP
            )
            if amendment_num is not None:
                amdt_no = amendment_num.text or ''
            if not amdt_no:
                # this happens in Lords running lists
                logger.info(f'No amendment number found for item with dnum: {dnum}')

            # Why do we remove the amendment number from the content again?
            amendment_num.getparent().remove(amendment_num)  # type: ignore
        except Exception as e:
            logger.error(
                f"Can't remove amendment number from amendment content {repr(e)}"
            )

        add_quotes_to_quoted_elements(amendment_content)

        # if (
        #     amendment_content.get('GUID', None)
        #     == '_2788704c-65ff-4413-aa67-644d7e32ea50'
        # ):
        #     logger.info('Found thing!')
        #     cleaned_whitespace = utils.clean_lm_xml_amdt(amendment_content)

        #     logger.info(etree.tostring(cleaned_whitespace, encoding='unicode'))
        #     text_content = xp.text_content(cleaned_whitespace)

        #     logger.info(f'Text content: {text_content}')

        #     normalised_text = utils.normalise_text(text_content)
        #     logger.info(f'Normalised text: {normalised_text}')

        amendment_text = utils.normalise_text(
            xp.text_content(utils.clean_lm_xml_amdt(amendment_content))
        )

        star = Star(amendment_xml.get(QName(UKL, 'statusIndicator'), default=''))

        _id = amendment_xml.xpath('.//*/@GUID[1]', namespaces=NSMAP)[0]
        # print(f"ID: {_id}")

        # if amdt_no.casefold().strip() == 'nc2':
        #     logger.info(f'Sponsors from XML: {repr(sponsors)}')

        return cls(
            amendment_text,
            explanatory_text,
            amdt_no,
            decision,
            sponsors,
            parent,
            star,
            _id,
            dnum,
        )


def normalise_amendments_xml(amendment_xml: _Element) -> _Element:
    raise NotImplementedError


def add_quotes_to_quoted_elements(amendment_element: _Element) -> None:
    """Element is modified in place"""

    # get the text
    # if there is a quoted structure there could be strangeness with quotes
    quoted_elements: list[_Element] = amendment_element.xpath(
        './/xmlns:*[@ukl:endQuote or @ukl:startQuote or @endQuote or @startQuote]',
        namespaces=NSMAP,
    )
    # print(f"Quoted Elements: {len(quoted_elements)}")
    for qs in quoted_elements:
        tag = QName(qs).localname
        if tag == 'def':
            # print(f'Def: {qs.text}')
            pass
            # print(qs.attrib)
        if qs.get('startQuote') == '“' or qs.get(f'{{{UKL}}}startQuote') == '“':
            if qs.text:
                qs.text = f'“{qs.text}'

            else:
                qs.text = '“'
        if qs.get('endQuote') == '”' or qs.get(f'{{{UKL}}}endQuote') == '”':
            if tag == 'quotedStructure':
                if qs.tail:
                    qs.tail = f'”{qs.tail}'
                else:
                    qs.tail = '”'
            else:
                if qs.text:
                    qs.text = f'{qs.text}”'
                else:
                    qs.text = '”'


class AmdtContainer(Mapping):
    """Container for an amendment document aka official list"""

    def __init__(
        self,
        amendments: list[Amendment],
        container_type: ContainerType = ContainerType.UNKNOWN,
        bill_title: str = 'Unknown Bill Title',
        pub_date: str = 'Unknown Published Date',
        resource_identifier: str = 'Unknown',
        bill_id: int | None = None,
        stage_id: int | None = None,
        stage_name: str | None = None,
    ):
        # move this to the javascript
        # self.short_file_name = utils.truncate_string(self.file_name).replace(".xml", "")

        # sometimes in the API there is more than one amendment with the same number
        # this causes problems when trying to compare the amendments
        self.duplicate_amdt_nums: list[str] = []

        # we really shouldn't have duplicate dnums but you never know with this data
        self.duplicate_amdt_keys: list[AmdtRef] = []

        # defaults for metadata
        self.container_type: ContainerType = container_type
        self.meta_bill_title: str = bill_title
        self.meta_pub_date: str = pub_date

        self.amendments = amendments
        self.resource_identifier = resource_identifier

        self.bill_id = bill_id
        self.stage_id = stage_id
        self.stage_name = stage_name

        self._dict: dict[AmdtRef, Amendment] = self._create_amdt_map()
        self.amdt_set: set[AmdtRef] = set(self._dict.keys())
        # {utils.clean_amendment_number(amdt.num) for amdt in self.amendments}

    @classmethod
    def blank_container(cls) -> 'AmdtContainer':
        return cls([])

    @classmethod
    def from_json(
        cls,
        json_data: dict[str, JSON],
        container_type: ContainerType = ContainerType.AMDTS_FROM_API,
        resource_identifier: str = 'Api Amendments',
    ) -> 'AmdtContainer':
        bill_id: int | None = json_data.get('billId', None)  # type: ignore
        stage_id: int | None = json_data.get('stageId', None)  # type: ignore
        stage_name: str | None = json_data.get('stageDescription', None)  # type: ignore
        bill_title: str = json_data.get('shortTitle', 'Unknown Bill Title')  # type: ignore

        amendments: list[Amendment] = []

        amendment_dicts = json_data.get('items', [])

        if not amendment_dicts:
            logger.error('No amendments found in JSON data')
            return cls([])

        for i, amendment in enumerate(amendment_dicts):  # type: ignore
            # amendmet_dicts can be completely empty
            # ... possibly http error when getting the amendments
            if len(amendment) == 0:
                logger.warning(f'Empty amendment JSON data at index {i}')
                continue
            try:
                amendment = Amendment.from_json(amendment)
                amendments.append(amendment)
            except InvalidDataError as e:
                logger.warning(repr(e))

        return cls(
            amendments,
            container_type=container_type,
            bill_title=bill_title,
            resource_identifier=resource_identifier,
            bill_id=bill_id,
            stage_id=stage_id,
            stage_name=stage_name,
        )

    @classmethod
    def from_xml_element(
        cls,
        xml_element: _Element,
        container_type: ContainerType = ContainerType.UNKNOWN,
        resource_identifier: str = 'XML',
    ) -> 'AmdtContainer':
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
    def from_xml_file(cls, xml_file: Path) -> 'AmdtContainer':
        resource_identifier = xml_file.name  # important
        file_path = str(xml_file.resolve())  # should this be location
        tree = etree.parse(file_path, parser=PARSER)
        root = tree.getroot()

        return cls.from_xml_element(
            root,
            resource_identifier=resource_identifier,
        )

    def get_meta_data_from_xml(self, root_element: _Element) -> None:
        try:
            list_type_text: str = root_element.findtext(
                ".//block[@name='listType']", namespaces=NSMAP2
            )  # type: ignore
            self.container_type = get_container_type(list_type_text)
            # self.meta_list_type = list_type.text  # type: ignore

        except AttributeError:
            logger.warning(f"Can't find the list type form the metadata in the XML.")

        except Exception as e:
            warning_msg = (
                f"Can't find List Type meta data. Check {self.resource_identifier}"
            )
            # self.meta_list_type = warning_msg  # should we add this back in?
            logger.warning(f'Problem parsing XML. {warning_msg}: {repr(e)}')

        try:
            # print(len(root_element.xpath('//xmlns:TLCConcept', namespaces=NSMAP)))
            bill_title = root_element.xpath(
                # TODO: if this works add it to the compare amendments documents
                "//xmlns:TLCConcept[@eId='varBillTitle']/@showAs",
                namespaces=NSMAP,
            )
            # don't use .get here  as that defaults to None
            # self.meta_bill_title = bill_title.attrib["showAs"]  # type: ignore
            self.meta_bill_title: str = bill_title[0]
            # [x] test
        except Exception as e:
            print(repr(root_element))
            warning_msg = (
                f"Can't find Bill Title meta data. Check {self.resource_identifier}"
            )
            self.meta_bill_title = warning_msg
            logger.warning(f'Problem parsing XML. {warning_msg}: {repr(e)}')

        try:
            # add a test for this
            published_date = root_element.find(
                ".//FRBRManifestation/FRBRdate[@name='published']", namespaces=NSMAP2
            )
            self.meta_pub_date = datetime.strptime(
                published_date.get('date', default=''),  # type: ignore
                '%Y-%m-%d',  # type: ignore
            ).strftime('%A %d %B %Y')

        except Exception as e:
            warning_msg = (
                f"Can't find Published Date meta data. Check {self.resource_identifier}"
            )
            self.meta_pub_date = warning_msg
            if not isinstance(e, AttributeError):
                warning_msg += f': {repr(e)}'
            logger.info(f'Problem parsing XML. {warning_msg}')

    def _create_amdt_map(self) -> dict[AmdtRef, Amendment]:
        _amdt_map: dict[AmdtRef, Amendment] = {}

        for amendment in self.amendments:
            if amendment.key in _amdt_map:
                self.duplicate_amdt_keys.append(amendment.key)
            _amdt_map[amendment.key] = amendment

        if len(self.duplicate_amdt_keys) > 0:
            logger.warning(
                f'The following amendment(s) in the {self.container_type} have '
                f' both same amendment num and dnums.'
                f' {", ".join(repr(key) for key in self.duplicate_amdt_keys)}'
                ' This should never happen and will confuse this app:'
            )

        return _amdt_map

    def __getitem__(self, key: AmdtRef) -> Amendment:
        if key in self._dict:
            return self._dict[key]
        for k in self._dict:
            if k.dnum == key.dnum:
                msg = f'Found amendment with matching dnum but different num: {k} vs {key}'
                # This can happen with lords running lists which do not
                # normally have amendment numbers...
                # it's possible that while the XML does not have amendment numbers
                # the API does have amendment numbers
                # (if updated since the XML was created)
                logger.info(msg)
                return self._dict[k]
        raise KeyError(f'Amendment with key {key} not found')

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
        json_amdts: dict[str, JSON],
        metadata: ReportMetadata | None = None,
    ):
        self.metadata = metadata

        if isinstance(xml, Path):
            self.xml_file_path: Path | None = xml
        else:
            self.xml_file_path = None

        try:
            self.html_tree = html.parse(COMPARE_REPORT_TEMPLATE)
            self.html_root = self.html_tree.getroot()
        except Exception as e:
            logger.error(f'Error parsing HTML template file: {e}')
            raise

        # create AmdtContainer object for xml amendments
        if isinstance(xml, Path):
            self.xml_amdts = AmdtContainer.from_xml_file(xml)
        elif iselement(xml):
            self.xml_amdts = AmdtContainer.from_xml_element(xml)
        else:
            raise TypeError('xml must be a Path or an Element')

        # create AmdtContainer object for json amendments
        self.json_amdts = AmdtContainer.from_json(json_amdts)

        # here we will put all amendments that arn't correctly in the API
        # including missing amendments, amendments with incorrect content,
        # amendments with incorrect names, incorrect decisions etc.
        # do we need this, could we not just add the other lists together?
        self.problem_amdts: list[ChangedAmdt] = []

        self.incorrect_amdt_in_api: list[ChangedAmdt] = []
        self.incorrect_decisions: list[str] = []  # change to list[Decision]
        self.correct_decisions: list[str] = []

        self.incorrect_ex_statements: list[str] = []  # change to list[AndtRef]

        self.missing_api_amdts: list[AmdtRef] = []

        self.no_name_changes: list[str] = []
        self.name_changes: list[ChangedNames] = []
        # self.duplicate_names: list[str] sp= []
        self.duplicate_names_in_xml: list[Sponsor] = []
        self.duplicate_names_in_api: list[Sponsor] = []

        self.name_changes_in_context: list[ChangedAmdt] = []

        self.correct_stars: list[str] = []
        self.incorrect_stars: list[str] = []  # change to list[Star]

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

        msg = 'Amendments in XML and not in API:'
        in_xml_but_not_api = self.xml_amdts.amdt_set - self.json_amdts.amdt_set
        logger.info(f'{msg} {[item.short_ref for item in in_xml_but_not_api]}')

        msg = 'Amendments in API and not in XML:'
        in_api_but_not_xml = self.json_amdts.amdt_set - self.xml_amdts.amdt_set
        logger.info(f'{msg} {[item.short_ref for item in in_api_but_not_xml]}')

        msg = 'Amendments which appear in both:'
        appears_in_both_set = self.xml_amdts.amdt_set & self.json_amdts.amdt_set
        logger.info(f'{msg} {[item.short_ref for item in appears_in_both_set]}')

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
            self.diff_ex_statements(xml_amdt, json_amend)

    def make_html(self):
        """
        Build up HTML document with various automated checks on amendments
        """

        try:
            # change the title
            self.html_root.find('.//title').text = 'Check Amendments'  # type: ignore
            self.html_root.find(
                './/h1'
            ).text = 'Check Amendments on Bills.parliament.uk'  # type: ignore
        except Exception:
            pass

        xp = './/div[@id="content-goes-here"]'
        insert_point: HtmlElement = self.html_root.find(xp)  # type: ignore
        # print(etr)
        insert_point.extend(
            (
                self.render_intro(),
                self.render_duplicate_amdt_nos(),
                self.render_duplicate_amdt_keys(),
                self.render_missing_amdts(),
                self.render_added_and_removed_names(),
                self.render_stars(),
                self.render_changed_amdts(),
                self.render_decisions(),
                self.render_ex_statements(),
            )
        )

    def render_intro(self) -> HtmlElement:
        # ------------------------- intro section ------------------------ #
        into = (
            'This report summarises differences between amendments in the '
            '<a href="https://bills-api.parliament.uk/index.html">bills API</a> and the amendments in the LawMaker document'
            ' XML official list documents. The document is:'
            f'<br><strong>{self.xml_amdts.meta_bill_title}</strong>'
        )

        meta_data_table = templates.Table(('', self.xml_amdts.meta_bill_title))

        # meta_data_table.add_row(
        #     ("File path", self.xml_amdts.file_path)
        # )
        meta_data_table.add_row(('Bill Title', self.xml_amdts.meta_bill_title))
        meta_data_table.add_row(('Published date', self.xml_amdts.meta_pub_date))
        meta_data_table.add_row(('List Type', self.xml_amdts.container_type))

        section = html.fromstring(
            '<div class="wrap">'
            '<section id="intro">'
            '<h2>Introduction</h2>'
            f'<p>{into}</p>'
            '</section>'
            '</div>'
        )

        section.append(meta_data_table.html)

        # Add optional metadata as an unordered list below the table
        if self.metadata:
            metadata_items: list[str] = []

            if self.metadata.lm_project_title:
                metadata_items.append(
                    f'<li>LawMaker Project: {self.metadata.lm_project_title}</li>'
                )
            if self.metadata.lm_stage:
                metadata_items.append(
                    f'<li>LawMaker Stage: {self.metadata.lm_stage}</li>'
                )
            if self.metadata.api_stage_description:
                # Build hyperlink if we have both bill_id and stage_id
                if self.metadata.api_bill_id and self.metadata.api_stage_id:
                    stage_url = (
                        f'https://bills.parliament.uk/bills/'
                        f'{self.metadata.api_bill_id}/stages/'
                        f'{self.metadata.api_stage_id}/amendments'
                    )
                    stage_link = (
                        f'<a href="{stage_url}" target="_blank">'
                        f'{self.metadata.api_stage_description}</a>'
                    )
                    metadata_items.append(
                        f'<li>Matched stage on parliament website (via bills API): {stage_link}</li>'
                    )
                else:
                    metadata_items.append(
                        f'<li>Matched stage on parliament website (via Bills API): '
                        f'{self.metadata.api_stage_description}</li>'
                    )
            if self.metadata.official_list_label:
                metadata_items.append(
                    f'<li>Official List: {self.metadata.official_list_label}</li>'
                )
            if self.metadata.generation_timestamp:
                dt = self.metadata.generation_timestamp
                timestamp_str = (
                    f'{dt.strftime("%a")} {dt.strftime("%d %B %Y %H:%M").lstrip("0")}'
                )

                metadata_items.append(f'<li>Report Generated: {timestamp_str}</li>')

            if metadata_items:
                metadata_list = html.fromstring(
                    f'<ul class="metadata-list">{"".join(metadata_items)}</ul>'
                )
                section.append(metadata_list)

        return section

    def render_duplicate_amdt_nos(self) -> HtmlElement:
        duplicate_xml_amdts = len(self.xml_amdts.duplicate_amdt_nums) > 0
        duplicate_api_amdts = len(self.json_amdts.duplicate_amdt_nums) > 0

        if not duplicate_xml_amdts and not duplicate_api_amdts:
            # noting to show so just return an empty div
            return html.Element('div')

        info = (
            '<p>Amendment numbers should be unique. The following amendment'
            ' numbers are repeated. <span class="red">This should never'
            ' happen</span>.</p>'
        )
        card = templates.Card('Duplicate amendment numbers')

        if duplicate_xml_amdts:
            info += '<p>XML Amendments:</p><p>'
            for num in self.xml_amdts.duplicate_amdt_nums:
                info += f'{num}<br/>'
            info += '</p>'

        if duplicate_api_amdts:
            info += '<p>API Amendments:</p><p>'
            for num in self.json_amdts.duplicate_amdt_nums:
                view_online = ''
                if self.json_amdts.bill_id and self.json_amdts.stage_id:
                    link = (
                        'https://bills.parliament.uk/bills/'
                        f'{self.json_amdts.bill_id}/stages/'
                        f'{self.json_amdts.stage_id}/amendments'
                        f'?searchTerm=&amendmentNumber={num}&Decision=All'
                    )
                    view_online = f'(<a href="{link}">View online</a>)'
                info += f'{num}  {view_online}<br/>'
            info += '</p>'

        card.secondary_info.extend(
            html.fragments_fromstring(info, no_leading_text=True)
        )
        return card.html

    def render_duplicate_amdt_keys(self) -> HtmlElement:
        duplicate_xml_amdts = len(self.xml_amdts.duplicate_amdt_keys) > 0
        duplicate_api_amdts = len(self.json_amdts.duplicate_amdt_keys) > 0

        if not duplicate_xml_amdts and not duplicate_api_amdts:
            # noting to show so just return an empty div
            return html.Element('div')

        info = (
            '<p>Amendment d numbers should be unique. The following amendment'
            ' d numbers are repeated. <span class="red">This should never'
            ' happen</span>.</p>'
        )
        card = templates.Card('Duplicate amendment d numbers')

        if duplicate_xml_amdts:
            info += '<p>XML Amendments:</p><p>'
            for num in self.xml_amdts.duplicate_amdt_keys:
                info += f'{num}<br/>'
            info += '</p>'

        if duplicate_api_amdts:
            info += '<p>API Amendments:</p><p>'
            for num in self.json_amdts.duplicate_amdt_keys:
                view_online = ''
                if self.json_amdts.bill_id and self.json_amdts.stage_id:
                    link = (
                        'https://bills.parliament.uk/bills/'
                        f'{self.json_amdts.bill_id}/stages/'
                        f'{self.json_amdts.stage_id}/amendments'
                        f'?searchTerm=&amendmentNumber={num}&Decision=All'
                    )
                    view_online = f'(<a href="{link}">View online</a>)'
                info += f'{num}  {view_online}<br/>'
            info += '</p>'

        card.secondary_info.extend(
            html.fragments_fromstring(info, no_leading_text=True)
        )
        return card.html

    def render_missing_amdts(self) -> HtmlElement:
        # ----------- Removed and added amendments section ----------- #
        # build up text content
        removed_content = 'Missing amendments: <strong>None</strong>'

        if self.missing_api_amdts:
            missing_amdt_reference: list[str] = []
            for key in self.missing_api_amdts:
                xml_amdt: Amendment | None = self.xml_amdts.get(key)
                if xml_amdt is None:
                    continue
                missing_amdt_reference.append(xml_amdt.key.long_ref)
                '--Satpal replaced parenthese'

            removed_content = (
                f'Missing content: <strong>{len(self.missing_api_amdts)}</strong><br/>'
            )
            if missing_amdt_reference:
                removed_content += ', '.join(missing_amdt_reference)

        info = (
            '<p>Listed below are any Amendments (& New Clauses etc.) which are'
            ' present in the XML from LawMaker but not present in Amendments'
            ' avaliable via the API. This means that they '
            ' also missing from the Bills website. </p>'
        )

        card = templates.Card('Missing amendments')
        card.secondary_info.extend(
            # html.fromstring(f"<p>{added_content}</p>"),
            html.fragments_fromstring(
                f'{info}<p>{removed_content}</p>', no_leading_text=True
            )
        )
        return card.html

    def added_and_removed_names_table(self) -> HtmlElement:
        if not self.name_changes:
            return html.fromstring(
                '<p><strong>Zero</strong> amendments have name changes.</p>'
            )

        name_changes = templates.Table(
            ('Ref', 'Names missing from API', 'Names in API but not in XML', 'Totals')
        )

        # we have a special class for this table
        name_changes.html.classes.add('an-table')  # type: ignore

        for item in self.name_changes:
            names_added = []
            names_removed = []

            for name in item.added:
                names_added.append(
                    html.fromstring(
                        f'<span class="col-12 col-lg-6  mb-2">{name}</span>'
                    )
                )
            p_names_added = html.fromstring('<p class="row"></p>')
            p_names_added.extend(names_added)

            for name in item.removed:
                names_removed.append(
                    html.fromstring(
                        f'<span class="col-12 col-lg-6  mb-2">{name}</span>'
                    )
                )
            p_names_removed = html.fromstring('<p class="row"></p>')
            p_names_removed.extend(names_removed)

            total_added = len(item.added)
            total_removed = len(item.removed)
            totals = []
            if total_added:
                totals.append(f'XML only: {total_added}')
            if total_removed:
                totals.append(f'API only: {total_removed}')

            name_changes.add_row(
                # put in long ref
                (item.num, p_names_added, p_names_removed, ', '.join(totals))
            )

        return name_changes.html

    def render_added_and_removed_names(self) -> HtmlElement:
        """Added and removed names section"""

        no_name_changes: HtmlElement | None = None

        if self.no_name_changes:
            sec = templates.SmallCollapsableSection(
                f'<span><strong>{len(self.no_name_changes)}</strong>'
                f' amendments have correct names: '
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
                    f'<p><strong>{len(self.name_changes_in_context)}</strong> amendments'
                    ' have different names in the API: </p>\n'
                )
            )
            for item in self.name_changes_in_context:
                num_a = link_from_num_or_num(item.ref, self.xml_amdts)
                changed_amdts.append(
                    html.fromstring(
                        f"<div><p class='h5 mt-4'>{num_a}:</p>\n{item.html_diff}\n</div>"
                    )
                )
        else:
            logger.info('No name changes in context')

        names_change_context_section.add_content(changed_amdts)

        if len(self.name_changes_in_context) == 0:
            # might as well not output anything if not necessary
            names_change_context_section.clear()

        card = templates.Card('Check Names')
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
            sec = templates.SmallCollapsableSection(
                f'<span><strong>{len(self.correct_stars)}</strong>'
                f' amendments have correct stars: '
                '<small class="text-muted"> [show]</small></span>'
            )
            sec.collapsible.text = f'{", ".join(self.correct_stars)}'
            correct_stars = sec.html

        incorrect_stars = 'All amendments have correct stars'
        if self.incorrect_stars:
            incorrect_stars = (
                f'<strong class="red">{len(self.incorrect_stars)} amendments'
                f' have incorrect stars:</strong>  {", ".join(self.incorrect_stars)}'
            )

        card = templates.Card('Star Check')
        card.secondary_info.append(html.fromstring(f'<p>{incorrect_stars}</p>'))
        if correct_stars is not None:
            card.tertiary_info.append(correct_stars)

        return card.html

    def render_changed_amdts(self) -> HtmlElement:
        # -------------------- Changed Amendments -------------------- #
        # build up text content
        changed_amdts = '<p>Amendments in the API match those in the XML 😀</p>'
        if self.incorrect_amdt_in_api:
            changed_amdts = (
                f'<p><strong class="red">{len(self.incorrect_amdt_in_api)}</strong>'
                ' amendments have incorrect content in the API: </p>\n'
            )
            for item in self.incorrect_amdt_in_api:
                num_a = link_from_num_or_num(
                    # TODO: change this to self.link_from_num_or_num
                    item.ref,
                    self.json_amdts,
                )
                changed_amdts += f"<p class='h5'>{num_a}:</p>\n{item.html_diff}\n"

        info = (
            '<p><strong>Note:</strong> There can be false'
            ' positives and some whitespace differences are ignored.</p>'
        )

        card = templates.Card('Incorrect amendments')
        card.secondary_info.extend(
            html.fragments_fromstring(f'{info}\n{changed_amdts}', no_leading_text=True)
        )

        return card.html

    def render_no_decision_check(self) -> HtmlElement:
        card = templates.Card('Decision Check')
        card.secondary_info.append(
            html.fromstring(
                '<p>The XML file does not appear to be a proceedings'
                ' paper so no decisions have been checked.</p>'
            )
        )
        return card.html

    def render_decisions(self) -> HtmlElement:
        # -------------------- Decision check section -------------------- #

        is_report_decisions = (
            self.xml_amdts.container_type == ContainerType.REPORT_DECISIONS
        )
        is_committee_decisions = (
            self.xml_amdts.container_type == ContainerType.COMMITTEE_DECISIONS
        )

        if not (is_report_decisions or is_committee_decisions):
            # logger.debug(f"{repr(self.xml_amdts.container_type)=}")
            return self.render_no_decision_check()

        # build up text content
        correct_decisions: HtmlElement | None = None

        if self.correct_decisions:
            sec = templates.SmallCollapsableSection(
                f'<span><strong>{len(self.correct_decisions)}</strong>'
                f' amendments in the API have decisions which match the'
                ' decision in the provided XML file: '
                '<small class="text-muted"> [show]</small></span>'
            )
            sec.collapsible.text = f'{", ".join(self.correct_decisions)}'
            correct_decisions = sec.html

        if self.incorrect_decisions:
            incorrect_decisions = (
                f'<p><strong class="red">{len(self.incorrect_decisions)}</strong>'
                ' amendments in the API have decisions which do not match the'
                ' decision in the provided XML file: </p>\n'
            )
            incorrect_decisions += f'<p>{"<br/>".join(self.incorrect_decisions)}</p>'
        else:
            incorrect_decisions = (
                '<p>Every decision (on all amendments) in the API matches'
                ' the decision in the XML. 😀</p>'
            )

        note = (
            '<p class="small"><strong>Note:</strong> For unknown reasons, decisions'
            ' recorded in a the proceedings paper do not map onto the decisions in'
            ' the API (and by extension, the amendments section of'
            ' bills.parliament.uk). For the purposes of this check the following'
            ' groups of decisions are considered to be the same:</p>'
        )
        list_items = [f'<li>{", ".join(l)}</li>' for l in Decision.similar_decisions]
        note += f"<ul class='small'>{''.join(list_items)}</ul>"

        card = templates.Card('Decision Check')
        card.secondary_info.append(
            html.fromstring(f'<div>{note + incorrect_decisions}</div>')
        )

        if correct_decisions is not None:
            card.tertiary_info.append(correct_decisions)

        return card.html

    def render_ex_statements(self) -> HtmlElement:
        # -------------------- Explanatory Statements -------------------- #
        # build up text content
        incorrect_ex_statements = (
            '<p>All explanatory statements in the API match those in the XML 😀</p>'
        )
        if self.incorrect_ex_statements:
            incorrect_ex_statements = (
                f'<p><strong class="red">{len(self.incorrect_ex_statements)}</strong>'
                ' amendments have incorrect explanatory statements in the API: </p>\n'
            )

            incorrect_ex_statements += (
                f'<p>{"<br/>".join(self.incorrect_ex_statements)}</p>'
            )

        card = templates.Card('Explanatory Statements')
        card.secondary_info.extend(
            html.fragments_fromstring(incorrect_ex_statements, no_leading_text=True)
        )

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
                # use short ref
                self.correct_stars.append(f'{api_amdt.key.short_ref} ({api_amdt.star})')
            else:
                self.incorrect_stars.append(
                    f'{api_amdt.key.short_ref} has {api_amdt.star} ({xml_amdt.star} expected)'
                )

    def added_and_removed_amdts(
        self, xml_amdts: 'AmdtContainer', json_amdts: 'AmdtContainer'
    ):
        """Find the amendment numbers missing from the API"""

        # self.xml_amdts, self.json_amdts)
        # old_doc: 'AmdtContainer', new_doc: 'AmdtContainer'

        logger.info(
            'Finding amendments missing from the API. '
            f'XML doc has {len(xml_amdts.amendments)} amendments, '
            f'JSON doc has {len(json_amdts.amendments)} amendments'
        )

        self.missing_api_amdts = list(
            xml_amdts.amdt_set.difference(json_amdts.amdt_set)
        )
        logger.info(f'Found {len(self.missing_api_amdts)} missing API amendments.')

        # we don't need amendments in the API but not in the document
        # self.added_amdts = list(new_doc.amdt_set.difference(old_doc.amdt_set))

    def diff_names(self, xml_amdt: Amendment, json_amdt: Amendment):
        # logger.debug(f'Finding differences in names for {xml_amdt.key}')
        # look for duplicate names. Only need to do this for the new_amdt.
        self.duplicate_names_in_api = find_duplicate_sponsors(json_amdt.sponsors)
        self.duplicate_names_in_xml = find_duplicate_sponsors(xml_amdt.sponsors)

        if self.duplicate_names_in_api:
            logger.warning(f'Duplicate names found in {json_amdt.key.long_ref} in API')
        if self.duplicate_names_in_xml:
            logger.warning(f'Duplicate names found in {xml_amdt.key.long_ref} in XML')

        added_names = [
            item.name for item in xml_amdt.sponsors if item not in json_amdt.sponsors
        ]
        removed_names = [
            item.name for item in json_amdt.sponsors if item not in xml_amdt.sponsors
        ]

        if not added_names and not removed_names:
            # there have been no name changes
            self.no_name_changes.append(xml_amdt.key.long_ref)
        else:
            self.name_changes.append(
                ChangedNames(
                    xml_amdt.key.long_ref, added_names, removed_names, xml_amdt.key
                )
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
            fromdesc='Lawmaker XML',
            todesc='Bills API',
        )

        if dif_html_str is not None:
            self.name_changes_in_context.append(ChangedAmdt(xml_amdt.key, dif_html_str))

    def diff_amdt_content(self, xml_amdt: Amendment, json_amdt: Amendment):
        """
        Create an HTML string containing a tables showing the differences
        between old_amdt//amendmentContent and new_amdt//amendmentContent.

        amendmentContent is the element which contains the text of the
        amendment. It does not contain the sponsor information.
        """
        # new_amdt = xml_amdt
        # old_amdt = json_amdt
        # called as self.diff_amdt_content(xml_amdt, json_amend)

        # When consecutive ”” make sure no new line between

        xml_amdt_content_fixed_quotes = utils.fix_consecutive_quotes(
            xml_amdt.amendment_text
        )
        json_amdt_content_fixed_quotes = utils.fix_consecutive_quotes(
            json_amdt.amendment_text
        )

        xml_amdt_content = xml_amdt_content_fixed_quotes.split('\n')
        json_amdt_content = json_amdt_content_fixed_quotes.split('\n')

        if len(xml_amdt_content) == 0 or len(json_amdt_content) == 0:
            # use the long ref
            logger.warning(f'{xml_amdt.key.long_ref}: has no content')
            return

        # sometimes the line breaks are different due to ref elements etc.
        # so first we will compare the text content with the line breaks
        # and other non-space whitespace removed
        xml_content_no_whitespace = re.sub(r'[^\S\s]+', '', ''.join(xml_amdt_content))
        json_content_no_whitespace = re.sub(r'[^\S\s]+', '', ''.join(json_amdt_content))

        # if xml_amdt.num == '18':
        #     print(xml_amdt_content_no_lines)
        #     print(json_amdt_content_no_lines)

        if xml_content_no_whitespace == json_content_no_whitespace:
            # use the long ref
            logger.debug(
                f'{xml_amdt.key.long_ref}: content the same when line breaks removed.'
            )
            return

        dif_html_str = utils.html_diff_lines(
            xml_amdt_content,
            json_amdt_content,
            fromdesc=self.xml_amdts.resource_identifier,
            todesc=self.json_amdts.resource_identifier,
        )
        if dif_html_str is not None:
            # short ref
            self.incorrect_amdt_in_api.append(ChangedAmdt(xml_amdt.key, dif_html_str))

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
            # try out both refs
            self.correct_decisions.append(xml_amdt.key.short_ref)
        else:
            self.incorrect_decisions.append(f'{xml_amdt.key.short_ref}')

    def diff_ex_statements(self, xml_amdt: Amendment, api_amdt: Amendment):
        """
        Check that the explanatory text in the API matches the explanatory
        text in the XML.
        """

        xml_ex = xml_amdt.explanatory_text
        api_ex = api_amdt.explanatory_text

        if not xml_ex:
            # no explanatory text in the XML so no point comparing
            return

        if utils.normalise_text(xml_ex) != utils.normalise_text(api_ex):
            # short ref
            self.incorrect_ex_statements.append(xml_amdt.key.short_ref)

    def all_clear(self) -> bool:
        """
        Check if there are any problems with the amendments.
        Returns True if there are no problems, False otherwise.
        """
        return all(
            # check that all lists of problems are empty
            len(i) == 0
            for i in (
                self.missing_api_amdts,
                self.incorrect_amdt_in_api,
                self.name_changes,
                self.incorrect_stars,
                self.incorrect_decisions,
                self.incorrect_ex_statements,
            )
        )

    def json_summary(self) -> dict[str, Any]:
        """
        Create a summary of the report in JSON format.
        """

        summary: dict[str, Any] = {
            'missing_amendments': [str(item) for item in self.missing_api_amdts],
            'incorrect_amendments': [item.ref for item in self.incorrect_amdt_in_api],
            'name_changes': [
                {
                    'ref': item.ref,
                    'added': item.added,
                    'removed': item.removed,
                }
                for item in self.name_changes
            ],
            'incorrect_stars': self.incorrect_stars,
            'incorrect_decisions': self.incorrect_decisions,
            'incorrect_explanatory_statements': self.incorrect_ex_statements,
        }

        return summary

    # def create_csv(self):
    #     # TODO: this needs some fixing
    #     if self.all_clear():
    #         logger.warning('No problems were found so no CSV file will be created.')
    #         return

    #     logger.notice(
    #         f'{len(self.missing_api_amdts)} Missing amendments.'
    #         f' {len(self.incorrect_amdt_in_api)} incorrect amendments.'
    #         f' {len(self.name_changes)} amendment have incorrect names.'
    #         f' {len(self.incorrect_stars)} amendments have incorrect stars.'
    #         f' {len(self.incorrect_decisions)} amendments have incorrect decisions.'
    #         f' {len(self.incorrect_ex_statements)} amendments have incorrect explanatory statements.'
    #     )

    #     missing_amendment_text = missing_amendment_guids = ''
    #     for item in self.missing_api_amdts:
    #         missing_amendment_text += f'{item}\n'
    #         missing_amendment_guids += f'{self.xml_amdts[item].id}\n'

    #     logger.debug('Created missing amendments text')

    #     incorrect_amendments_text = ''
    #     incorrect_amendment_guids = ''
    #     incorrect_amendment_links = ''
    #     for item in self.incorrect_amdt_in_api:
    #         # TODO: fix ChangedAmdt to use AmdtRef not str for num
    #         incorrect_amendments_text += f'{item.ref}\n'
    #         # long ref
    #         incorrect_amendment_guids += f'{self.xml_amdts[item.ref].id}\n'
    #         # TODO: fix this
    #         logger.info(url_from_num_or_na(item.ref, self.json_amdts))
    #         incorrect_amendment_links += (
    #             url_from_num_or_na(item.ref, self.json_amdts) + '\n'
    #         )

    #     logger.debug('Created incorrect amendments text')

    #     incorrect_names = ''
    #     incorrect_names_guids = ''
    #     incorrect_names_links = ''

    #     for item in self.name_changes:
    #         # short ref
    #         incorrect_names += f'{item.ref}\n'
    #         incorrect_names_guids += f'{self.xml_amdts[item.ref].id}\n'
    #         incorrect_names_links += (
    #             url_from_num_or_na(item.ref, self.json_amdts) + '\n'
    #         )

    #     logger.debug('Created incorrect names text')

    #     incorrect_stars = ''
    #     incorrect_stars_guids = ''

    #     for item in self.incorrect_stars:
    #         incorrect_stars += f'{item}\n'
    #         try:
    #             amdt_num = item.split(' has ')[0]
    #             incorrect_stars_guids += f'{self.xml_amdts[amdt_num].id}'
    #         except Exception as e:
    #             logger.error(f'Error getting GUID for {item}: {e}')

    #     logger.debug('Created incorrect stars text')

    #     incorrect_decisions = ''
    #     incorrect_decisions_guids = ''

    #     for item in self.incorrect_decisions:
    #         try:
    #             amdt_num = item.split(' (API: ')[0]
    #             num_a = link_from_num_or_num(amdt_num, self.json_amdts)
    #             i_text = item.replace(amdt_num, num_a)
    #             # logger.info(f"num_a: {num_a} amdt_num: {amdt_num} i_text: {i_text}")
    #             incorrect_decisions += f'{i_text}'
    #             incorrect_decisions_guids += f'{self.xml_amdts[amdt_num].id}\n'
    #         except Exception as e:
    #             logger.error(f'Error getting GUID for {item}: {e}')

    #     logger.debug('Created incorrect decisions text')

    #     incorrect_ex_statements = ''
    #     incorrect_ex_statements_guids = ''
    #     if len(self.incorrect_ex_statements) > 0:
    #         incorrect_ex_statements = (
    #             'Amendments with incorrect explanatory statements:\n'
    #         )
    #         incorrect_ex_statements_guids = incorrect_ex_statements
    #     for item in self.incorrect_ex_statements:
    #         num_a = link_from_num_or_num(item, self.json_amdts)
    #         incorrect_ex_statements += f'{num_a}\n'
    #         try:
    #             incorrect_ex_statements_guids += f'{self.xml_amdts[item].id}\n'
    #         except Exception as e:
    #             logger.error(f'Error getting GUID for {item}: {e}')

    #     data = [
    #         [
    #             'Bill',
    #             'Stage',
    #             'Amendment paper date',
    #             'Date row created',
    #             'Missing amendments',
    #             'Missing amendment GUIDs',
    #             'Incorrect amendments',
    #             'Incorrect amendment GUIDs',
    #             'Incorrect amendment link',
    #             'Incorrect names',
    #             'Incorrect names GUIDs',
    #             'Incorrect stars',
    #             'Incorrect stars GUIDs',
    #             'Incorrect decisions',
    #             'Incorrect decisions GUIDs',
    #             'Incorrect explanatory statements',
    #             'Incorrect explanatory statements GUIDs',
    #         ],
    #         [
    #             self.xml_amdts.meta_bill_title,
    #             self.xml_amdts.stage_name,
    #             self.xml_amdts.meta_pub_date,
    #             datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #             missing_amendment_text,
    #             missing_amendment_guids,
    #             incorrect_amendments_text,
    #             incorrect_amendment_guids,
    #             incorrect_amendment_links,
    #             incorrect_names,
    #             incorrect_names_guids,
    #             incorrect_stars,
    #             incorrect_stars_guids,
    #             incorrect_decisions,
    #             incorrect_decisions_guids,
    #             incorrect_ex_statements,
    #             incorrect_ex_statements_guids,
    #         ],
    #     ]

    #     bill_stage = self.json_amdts.stage_name
    #     xml_file_path = self.xml_file_path
    #     if xml_file_path:
    #         parent_path = xml_file_path.resolve().parent
    #     else:
    #         parent_path = Path.cwd()

    #     bill_title_text = self.xml_amdts.meta_bill_title

    #     if bill_stage is not None:
    #         file_name = f'{bill_title_text}_{bill_stage}_amdt_table.csv'
    #     else:
    #         file_name = f'{bill_title_text}_amdt_table.csv'

    #     file_path = parent_path / file_name

    #     with open(file_path, 'w', newline='') as f:
    #         writer = csv.writer(f)
    #         writer.writerows(data)

    #     logger.notice(f'CSV file created at {file_path}. ')

    def create_table_for_sharepoint(self):
        """
        Output a HTML table row suitable for coping into an existing sharepoint list
        """

        # build up the text strings
        bill_title_text = self.xml_amdts.meta_bill_title
        missing_amendment_text = ''
        missing_amendment_guids = ''

        if self.all_clear():
            logger.warning('No problems were found so no table will be created.')
            return

        logger.notice(
            f'{len(self.missing_api_amdts)} Missing amendments.'
            f' {len(self.incorrect_amdt_in_api)} incorrect amendments.'
            f' {len(self.name_changes)} amendment have incorrect names.'
            f' {len(self.incorrect_stars)} amendments have incorrect stars.'
            f' {len(self.incorrect_decisions)} amendments have incorrect decisions.'
            f' {len(self.incorrect_ex_statements)} amendments have incorrect explanatory statements.'
        )

        if len(self.missing_api_amdts) > 0:
            missing_amendment_guids = missing_amendment_text = (
                'Missing Amendments:<br/>'
            )

        for item in self.missing_api_amdts:
            missing_amendment_text += f'<p>{item}</p>'
            missing_amendment_guids += f'<p>{self.xml_amdts[item].id}</p>'

        logger.debug('Created missing amendments text')

        incorrect_amendments_text = ''
        incorrect_amendment_guids = ''
        if len(self.incorrect_amdt_in_api) > 0:
            incorrect_amendments_text = '<p><br/>Amendments with incorrect content:</p>'
            incorrect_amendment_guids = incorrect_amendments_text
        for item in self.incorrect_amdt_in_api:
            # do whatever we do with link
            num_a = link_from_num_or_num(item.ref, self.json_amdts)
            incorrect_amendments_text += f'<p>{num_a}</p>'
            incorrect_amendment_guids += f'<p>{self.xml_amdts[item.ref].id}</p>'

        logger.debug('Created incorrect amendments text')

        incorrect_names = ''
        incorrect_names_guids = ''
        if len(self.name_changes) > 0:
            incorrect_names = '<p><br/>Amendments with incorrect names:</p>'
            incorrect_names_guids = incorrect_names
        for item in self.name_changes:
            num_a = link_from_num_or_num(item.ref, self.json_amdts)
            incorrect_names += f'<p>{num_a}</p>'
            incorrect_names_guids += f'<p>{self.xml_amdts[item.ref].id}</p>'

        logger.debug('Created incorrect names text')

        incorrect_stars = ''
        incorrect_stars_guids = ''
        if len(self.incorrect_stars) > 0:
            incorrect_stars = '<p><br/>Amendments with incorrect stars:</p>'
            incorrect_stars_guids = incorrect_stars
        for item in self.incorrect_stars:
            incorrect_stars += f'<p>{item}</p>'
            try:
                amdt_num = item.split(' has ')[0]
                incorrect_stars_guids += f'<p>{self.xml_amdts[amdt_num].id}</p>'
            except Exception as e:
                logger.error(f'Error getting GUID for {item}: {e}')

        logger.debug('Created incorrect stars text')

        incorrect_decisions = ''
        incorrect_decisions_guids = ''
        if len(self.incorrect_decisions) > 0:
            incorrect_decisions = '<p><br/>Amendments with incorrect decisions:</p>'
            incorrect_decisions_guids = incorrect_decisions
        for item in self.incorrect_decisions:
            try:
                amdt_num = item.split(' (API: ')[0]
                num_a = link_from_num_or_num(amdt_num, self.json_amdts)
                i_text = item.replace(amdt_num, num_a)
                # logger.info(f"num_a: {num_a} amdt_num: {amdt_num} i_text: {i_text}")
                incorrect_decisions += f'<p>{i_text}</p>'
                incorrect_decisions_guids += f'<p>{self.xml_amdts[amdt_num].id}</p>'
            except Exception as e:
                logger.error(f'Error getting GUID for {item}: {e}')

        logger.debug('Created incorrect decisions text')

        incorrect_ex_statements = ''
        incorrect_ex_statements_guids = ''
        if len(self.incorrect_ex_statements) > 0:
            incorrect_ex_statements = (
                '<p><br/>Amendments with incorrect explanatory statements:<p/>'
            )
            incorrect_ex_statements_guids = incorrect_ex_statements
        for item in self.incorrect_ex_statements:
            num_a = link_from_num_or_num(item, self.json_amdts)
            incorrect_ex_statements += f'<p>{num_a}<p/>'
            try:
                incorrect_ex_statements_guids += f'<p>{self.xml_amdts[item].id}<p/>'
            except Exception as e:
                logger.error(f'Error getting GUID for {item}: {e}')

        problem_amendment_numbers = (
            missing_amendment_text
            + incorrect_amendments_text
            + incorrect_names
            + incorrect_stars
            + incorrect_decisions
            + incorrect_ex_statements
        )
        problem_amendment_guids = (
            missing_amendment_guids
            + incorrect_amendment_guids
            + incorrect_names_guids
            + incorrect_stars_guids
            + incorrect_decisions_guids
            + incorrect_ex_statements_guids
        )

        basic_html_doc = templates.basic_document
        try:
            main_element = basic_html_doc.xpath("//*[@id='main-content']")[0]
            if not isinstance(main_element, HtmlElement):
                raise ValueError('Main element not found.')
        except Exception as e:
            logger.error(f'Error getting main element: {e}')
            return

        # create an HTML table
        # table = templates.Table(
        #     table_headings=['Date and Time of issue', 'Bill', 'House', 'Stage', 'Amendment Numbers', 'GUIDs'],
        #     table_rows=[[
        #         datetime.now().strftime("%d/%m/%Y %H:%M"),
        #         bill_title_text,
        #         # TODO: add house and stage
        #         "",
        #         "",
        #         problem_amendment_numbers,
        #         problem_amendment_guids
        #     ]],
        # )

        # main_element.append(table.html)

        bill_title_e = html.fromstring('<h2>Bill</h2>')
        bill_text_e = templates.EditableTextDiv(bill_title_text)
        amdt_no_title_e = html.fromstring('<h2>Amendment numbers</h2>')
        amdt_no_text_e = templates.EditableTextDiv(
            children=html.fragments_fromstring(problem_amendment_numbers)  # type: ignore
        )
        guids_title_e = html.fromstring('<h2>Amendments GUIDs</h2>')
        guids_text_e = templates.EditableTextDiv(
            children=html.fragments_fromstring(problem_amendment_guids)  # type: ignore
        )

        date_title_e = html.fromstring('<h2>Date and time of issue</h2>')
        date_text_e = templates.EditableTextDiv(
            datetime.now().strftime('%d/%m/%Y %H:%M')
        )

        stage_title_e = html.fromstring('<h2>Stage</h2>')
        stage_text_e = templates.EditableTextDiv(f'{self.json_amdts.stage_name}')

        main_element.extend(
            [
                item if isinstance(item, HtmlElement) else item.html
                for item in (
                    bill_title_e,
                    bill_text_e,
                    amdt_no_title_e,
                    amdt_no_text_e,
                    guids_title_e,
                    guids_text_e,
                    date_title_e,
                    date_text_e,
                    stage_title_e,
                    stage_text_e,
                )
            ]
        )

        tree = etree.ElementTree(basic_html_doc)

        bill_stage = self.json_amdts.stage_name
        xml_file_path = self.xml_file_path
        if xml_file_path:
            parent_path = xml_file_path.resolve().parent
        else:
            parent_path = Path.cwd()

        if bill_stage is not None:
            file_name = f'{bill_title_text}_{bill_stage}_amdt_table.html'
        else:
            file_name = f'{bill_title_text}_amdt_table.html'

        file_path = parent_path / file_name

        tree.write(
            str(file_path),
            pretty_print=True,
            method='html',
            doctype='<!DOCTYPE html>',
            encoding='utf-8',
        )

        webbrowser.open(file_path.resolve().as_uri())


def sync_query_bills_api(
    amend_xml_path: Path, save_json: bool = True
) -> dict[str, JSON] | None:
    """
    Synchronous wrapper for async_query_bills_api.
    """

    return asyncio.run(async_query_bills_api(amend_xml_path, save_json))


async def async_query_bills_api(
    amend_xml_path: Path, save_json: bool = True
) -> dict[str, JSON] | None:
    """
    Query the API for the bill XML files related to the amendment XML file.
    """

    if not amend_xml_path:
        logger.error('No amendment XML file selected.')
        return

    amend_xml = pp_xml_lxml.load_xml(str(amend_xml_path))

    if not amend_xml:
        logger.error(f'Amendment XML file is not valid XML: {amend_xml_path}')
        return

    # find the bill title from the amendment XML
    amdt_xml_root = amend_xml.getroot()
    try:
        bill_title = amdt_xml_root.xpath(
            '//xmlns:TLCConcept[@eId="varBillTitle"]/@showAs', namespaces=NSMAP
        )[0]
        logger.info(f'Bill title found in XML: {bill_title}')

    except Exception as e:
        logger.error("Could not find bill title in amendment XML. Can't query API.")
        logger.error(repr(e))
        return

    # try:
    #     # url encode the title
    #     bill_title = urllib.parse.quote(bill_title)
    #     url = f'https://bills-api.parliament.uk/api/v1/Bills?SearchTerm={bill_title}&SortOrder=DateUpdatedDescending'
    #     logger.info(f'Querying: {url}')
    #     response = SESSION.get(url, timeout=DEFAULT_TIMEOUT)
    #     response.raise_for_status()
    #     response_json: JSONObject = response.json()
    # except RequestException as e:
    #     logger.error(f'Error querying the API: {e}')
    #     return

    async with bills_api.BillsApiClient() as client:
        # TODO: remember to normalise the bill title
        _bill_title = urllib.parse.quote(bill_title)
        try:
            bills = await client.get_bills(search_term=_bill_title)
        except Exception as e:
            logger.error(f'Error querying the API asynchronously: {e}')
            return

    # file_name = "amendments_details.json"
    # json.dump(response_json, open(file_name, "w"), indent=2, ensure_ascii=False)
    # logger.info(Path(file_name).resolve())

    # bills: list = response_json.get('items', [])

    if not bills:
        logger.error(f'No bills found in the API with the title "{bill_title}"')
        return
    if len(bills) > 1:
        logger.warning(
            f'{len(bills)} bills found in the API with the query "{bill_title}".'
            ' Using the first bill found.'
        )

    # bill_json = bills[0]
    bill = bills[0]

    # try to get the stage from the xml
    stage: str | None = utils.get_stage_from_amdts_xml(amdt_xml_root)
    if not stage:
        logger.error('Could not find stage in amendment XML. Cannot query API.')
        return

    # TODO: fix this

    api_stage_description = bill.current_stage_description
    api_bill_short_title = bill.short_title
    bill_id: int | None = bill.bill_id
    stage_id: int | None = bill.current_stage_id

    if stage.casefold().strip() != api_stage_description.casefold().strip():
        logger.info(
            f'Stage in amendment XML ({stage}) does not match current stage in API ({api_stage_description}).'
        )
        # look thorugh all other stages to get the correct one
        try:
            url = f'https://bills-api.parliament.uk/api/v1/Bills/{bill_json["billId"]}/Stages'
            response = SESSION.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            response_json = response.json()
            stages = response_json.get('items', [])
            for item in stages:  # type: ignore
                description = item.get('description', '')
                if description.casefold().strip() == stage.casefold().strip():
                    api_stage_description = description
                    stage_id = item.get('id', None)
                    logger.notice(
                        f'Stage found in API: {api_stage_description}. Stage ID: {stage_id}'
                    )
                    break
        except Exception as e:
            logger.error('Error getting stages from API.')
            logger.error(repr(e))

    logger.notice(f'Bill ID: {bill_id} Stage ID: {stage_id}')

    if not (isinstance(bill_id, int) and isinstance(stage_id, int)):
        logger.error('Could not get bill ID or stage ID from the API.')
        return

    async with bills_api.BillsApiClient() as client:
        amendments_summary_json = await get_amendments_summary_json(
            bill_id, stage_id, client
        )
        amdts_json = get_amendments_detailed_json(
            amendments_summary_json,
            bill_id,
            stage_id,
            api_stage_description,
            api_bill_short_title,
        )

    if save_json:
        _short_title = clean_filename(api_bill_short_title, file_name_safe=True)
        _stage = clean_filename(api_stage_description, file_name_safe=True)
        file_name = f'{_short_title}_{_stage}_amdts.json'
        # file_name = create_friendly_name(file_name, lowercase=False)
        xml_file_parent = amend_xml_path.parent
        file_path = xml_file_parent / file_name

        try:
            with open(file_path, 'w') as f:
                json.dump(amdts_json, f, indent=2, ensure_ascii=False)
            logger.notice(f'Amendments details saved to file: {file_path}')
        except Exception as e:
            logger.error(f'Could not save amendments JSON to file: {file_path}')
            logger.error(repr(e))

    return amdts_json


def save_json_to_file(json_data: dict[str, JSON], file_path: Path) -> None:
    """
    Save the JSON data to a file.
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.notice(f'Amendments details saved to file: {file_path}')
    except Exception as e:
        logger.error(f'Could not save amendments JSON to file: {file_path}')
        logger.error(repr(e))


def create_friendly_name(text: str, lowercase: bool = True) -> str:
    # Remove all non-alphanumeric characters (excluding underscores if needed)
    cleaned = re.sub(r'[^A-Za-z0-9]', '', text)
    return cleaned.lower() if lowercase else cleaned


async def get_amendments_detailed_json(
    amendments_summary_json: list[JSONObject],
    bill_id: int,
    stage_id: int,
    client: bills_api.BillsApiClient,
    stage_description: str = '',
    api_bill_short_title: str = '',
) -> JSONObject:
    """
    Fetch detailed amendment information from the Bills API.

    Takes a list of amendment summaries and retrieves full details for each
    amendment by making concurrent API requests.

    Args:
        amendments_summary_json: List of amendment summary objects from the API.
        bill_id: The unique identifier for the bill.
        stage_id: The unique identifier for the bill stage.
        stage_description: Human-readable description of the stage (e.g., 'Committee').
        api_bill_short_title: The short title of the bill.

    Returns:
        A dictionary containing the bill metadata and a list of detailed amendment
        objects under the 'items' key.

    Raises:
        May log errors for failed requests but continues processing
        remaining amendments.
    """
    json_amendments_list: list[JSONType] = []

    amendment_ids = [
        amendment.get('amendmentId', 0) for amendment in amendments_summary_json
    ]
    logger.info(f'{len(amendment_ids)=}')
    # logger.info(f'{amendment_ids=}')

    tasks = [
        client.get_amendment_json(bill_id, stage_id, amdt_id)
        for amdt_id in amendment_ids
    ]

    results = await async_progress_bar(
        tasks, error_prefix='Amendment detail fetch failed'
    )

    for result in results:
        if isinstance(result, Exception):
            logger.error(f'Error fetching amendment detail: {result}')
            continue
        json_amendments_list.append(result)

    # def _request_data(amendment_id: str):
    #     """Query the API using the shared SESSION and return response or None."""
    #     url = f'https://bills-api.parliament.uk/api/v1/Bills/{bill_id}/Stages/{stage_id}/Amendments/{amendment_id}'
    #     try:
    #         resp = SESSION.get(url, timeout=DEFAULT_TIMEOUT)
    #         resp.raise_for_status()
    #         return resp
    #     except Exception as e:
    #         logger.error(f'Error fetching amendment {amendment_id}: {e}')
    #         return None

    # max_workers = min(10, max(2, len(amendment_ids)))
    # with ThreadPoolExecutor(max_workers=max_workers) as pool:
    #     # create a progress bar and return a list
    #     responses = progress_bar(
    #         pool.map(lambda amendment_id: _request_data(amendment_id), amendment_ids),
    #         len(amendment_ids),
    #     )
    #     print()  # newline after progress bar

    # logger.info(f'{responses=}')
    # json_amendments_list: list[JSONType] = []
    # for response in responses:
    #     if response is None:
    #         # keep a placeholder empty object to maintain list lengths
    #         json_amendments_list.append({})
    #         continue
    #     try:
    #         json_amendments_list.append(response.json())
    #     except Exception as e:
    #         logger.error(f'Error parsing JSON response: {e}')
    #         json_amendments_list.append({})

    json_output = {
        'shortTitle': api_bill_short_title,
        'billId': bill_id,
        'stageId': stage_id,
        'stageDescription': stage_description,
        'items': json_amendments_list,
    }

    return json_output


async def get_amendments_summary_json(
    bill_id: int,
    stage_id: int,
    client: bills_api.BillsApiClient,
    store_json_path: Path | None = None,
) -> list[JSONObject]:
    # run the first query synchronously to get the total count
    # url = AMENDMENTS_URL_TEMPLATE.format(bill_id=bill_id, stage_id=stage_id, skip=0)
    # response_json = get_json_sync(url)

    response_json = client.get_amendments_json(bill_id, stage_id, skip=0, take=20)

    json_amendments: list[JSONObject] = response_json.get('items')  # type: ignore

    total_results: int = response_json.get('totalResults', 0)  # type: ignore

    print(f'Total Amendments found in API: {total_results}')

    number_of_requests = math.ceil(total_results / 20)

    tasks = [
        client.get_amendments_json(bill_id, stage_id, skip=i * 20, take=20)
        for i in range(1, number_of_requests)
    ]

    # urls = [
    #     AMENDMENTS_URL_TEMPLATE.format(bill_id=bill_id, stage_id=stage_id, skip=i * 40)
    #     for i in range(1, number_of_requests)
    # ]
    logger.info(f'No. of tasks: {len(tasks)}')

    results = await async_progress_bar(tasks, error_prefix='Amendment fetch failed')

    for result in results:
        if isinstance(result, Exception):
            logger.error(f'Error fetching amendments summary: {result}')
            continue
        json_amendments += result.get('items', [])  # type: ignore

    # responses: list[JSONObject] = []
    # max_workers = min(10, max(2, len(urls)))
    # with ThreadPoolExecutor(max_workers=max_workers) as pool:
    #     # create a progress bar and return a list
    #     responses = progress_bar(pool.map(get_json_sync, urls), len(urls))
    #     print()  # newline after progress bar

    # if store_json_path is not None:
    #     with open(store_json_path, 'w') as f:
    #         json.dump(responses, f, indent=2, ensure_ascii=False)

    # for response in responses:
    #     if response.get('items', []):
    #         json_amendments += response.get('items', [])

    return json_amendments


def link_from_num_or_num(
    amendment_ref: AmdtRef, api_amendment_container: AmdtContainer
) -> str:
    """
    Create a hyperlink to the amendment on the bills.parliament.uk website.
    """

    url = get_url_for_amendment(amendment_ref, api_amendment_container)

    if not url:
        return amendment_ref.short_ref

    return create_hyperlink_str(url, amendment_ref.short_ref)


def url_from_num_or_na(
    amendment_ref: AmdtRef, api_amendment_container: AmdtContainer
) -> str:
    """
    Create a hyperlink to the amendment on the bills.parliament.uk website.
    If the amendment is not found, return 'N/A'.
    """

    url = get_url_for_amendment(amendment_ref, api_amendment_container)

    if not url:
        return 'N/A'

    return url


def create_hyperlink_str(url: str, text: str) -> str:
    return f'<a href="{url}" target="_blank">{text}</a>'


def get_url_for_amendment(
    amendment_ref: AmdtRef, api_amendment_container: AmdtContainer
) -> str | None:
    """
    Create a hyperlink to the amendment on the bills.parliament.uk website.
    """
    bill_id = api_amendment_container.bill_id
    stage_id = api_amendment_container.stage_id

    if not bill_id or not stage_id:
        # logger.info(f"{bill_id=} {stage_id=}")
        return

    try:
        amdt_object = api_amendment_container[amendment_ref]
    except KeyError:
        logger.info(f'{amendment_ref} not in {api_amendment_container}')
        return

    amendment_id = amdt_object.id
    if not amendment_id:
        logger.info(f'{repr(amendment_id)} not there')
        return

    url = f'https://bills.parliament.uk/bills/{bill_id}/stages/{stage_id}/amendments/{amendment_id}'

    return url


def find_duplicate_sponsors(lst: list[Sponsor]) -> list[Sponsor]:
    """
    Find and return a list of duplicate items in the given list.

    This function takes a list of strings and returns a list of items that
    appear more than once in the original list. The returned list contains
    the duplicate items sorted in ascending order.
    """

    # Convert the list to a set to remove duplicates
    unique_items = []
    duplicate_items = []

    for sponsor in lst:
        if sponsor in unique_items:
            if sponsor not in duplicate_items:
                duplicate_items.append(sponsor)
        else:
            unique_items.append(sponsor)

    # logger.info(f'{unique_items=}')
    # logger.info(f'{duplicate_items=}')

    return duplicate_items


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Compare amendments between an XML file and the API.'
        ' If no JSON file is provided, the API will be queried automatically.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s amendments.xml
  %(prog)s amendments.xml --json amendments.json
  %(prog)s amendments.xml -o report.html
  %(prog)s amendments.xml --sp
        """,
    )
    parser.add_argument(
        'xml_file',
        type=Path,
        help='XML amendment or proceedings file path',
    )
    parser.add_argument(
        '--json',
        type=Path,
        metavar='json_file',
        default=None,
        help='Existing JSON file with amendments details',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        metavar='OUTPUT_FILE',
        default=None,
        help='Where to save the output report HTML file',
    )
    parser.add_argument(
        '--sp',
        action='store_true',
        help='Create a table for SharePoint instead of the full report',
    )
    parser.add_argument(
        '--no-save-json',
        action='store_true',
        help='Do not save JSON response to file when querying API',
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Save a JSON summary of amendments to a file',
    )
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not attempt to open the report in a web browser',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='Increase verbosity (use -vv for debug level)',
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )
    args = parser.parse_args()

    return args


def setup_logging(verbosity: int):
    """Setup logging based on verbosity level."""

    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    # set the logging level for the console handler
    for handler in logger.handlers:
        if not isinstance(handler, logging.StreamHandler):
            continue
        handler.setLevel(level)
    # logger.setLevel(level)  # dont need this as already set to DEBUG


def main():
    lawchecker_logger.setup_lawchecker_logging()
    try:
        args = parse_arguments()

        # Validate arguments
        if (error_code := validate_arguments(args)) != 0:
            return error_code

        # Load or fetch amendments data
        if args.json:
            logger.info(f'Loading amendments from JSON file: {args.json}')
            try:
                with args.json.open('r') as f:
                    amendments_list_json = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f'Invalid JSON file {args.json}: {e}')
                return 1
            except Exception as e:
                logger.error(f'Error reading JSON file {args.json}: {e}')
                return 1
        else:
            logger.info('Querying API for amendments data...')
            save_json = not args.no_save_json
            amendments_list_json = sync_query_bills_api(args.xml_file, save_json)

        if not amendments_list_json:
            logger.error('No amendments found from JSON file or API.')
            return 1

        # Parse XML file
        logger.info(f'Parsing XML file: {args.xml_file}')
        try:
            with args.xml_file.open('rb') as f:
                tree = etree.parse(f, parser=PARSER)
            root = tree.getroot()
        except Exception as e:
            logger.error(f'Error parsing XML file {args.xml_file}: {e}')
            return 1

        # Find amendments in XML
        xpath = "//xmlns:amendment[@name='hcamnd']/xmlns:amendmentBody[@eId]"
        amendments_xml = root.xpath(xpath, namespaces=NSMAP)
        logger.info(f'Found {len(amendments_xml)} amendments in XML')

        # Generate report
        logger.info('Generating report...')
        report = Report(root, amendments_list_json)

        # Determine output filename
        if args.output:
            output_file: Path = args.output
        else:
            output_file: Path = args.xml_file.with_suffix('.html')

        if args.summary:
            summary_json_file = output_file.with_name(
                output_file.stem + '_summary.json'
            )
            with summary_json_file.open('w') as f:
                json.dump(report.json_summary(), f, indent=2, ensure_ascii=False)
            logger.info(f'Saved summary JSON file to: {summary_json_file}')
        else:
            logger.info('Skipping summary JSON file as --summary not specified.')

        # Generate appropriate output
        if args.sp:
            logger.info('Creating SharePoint table...')
            report.create_table_for_sharepoint()
        else:
            report.html_tree.write(
                str(output_file),
                method='html',
                encoding='utf-8',
                doctype='<!DOCTYPE html>',
            )

            msg = f'Wrote HTML report to: {output_file}'
            print(msg)
            logger.info(msg)

            if not args.no_browser:
                # Open in browser if possible
                webbrowser.open(output_file.resolve().as_uri())

    except KeyboardInterrupt:
        logger.warning('Process interrupted by user. Exiting.')
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return 1

    return 0


def validate_arguments(args):
    """Validate command line arguments and return error code if invalid."""
    if not args.xml_file.exists():
        logger.error(f'XML file does not exist: {args.xml_file}')
        return 1

    if not args.xml_file.is_file():
        logger.error(f'XML path is not a file: {args.xml_file}')
        return 1

    if not os.access(args.xml_file, os.R_OK):
        logger.error(f'XML file is not readable: {args.xml_file}')
        return 1

    if args.json and not args.json.exists():
        logger.error(f'JSON file does not exist: {args.json}')
        return 1

    if args.output:
        output_dir = args.output.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f'Cannot create output directory {output_dir}: {e}')
                return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
