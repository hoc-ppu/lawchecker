#!/usr/bin/env python3

"""
Shared container classes for a LawMaker XML official list document (amendment
paper) and the individual amendments within it.

These are used by both compare_amendment_documents.py and
duplicate_amendments.py.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Literal

from lxml import etree
from lxml.etree import QName, _Element

from lawchecker import xpath_helpers as xp
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import NSMAP, NSMAP2, PARSER, UKL, XMLNS
from lawchecker.stars import Star
from lawchecker.utils import truncate_string

MetadataName = Literal[
    'List Type',
    'Bill Title',
    'Published Date',
    'House',
    'Stage',
]


@dataclass(frozen=True)
class Heading:
    """
    A heading on an amendment paper, e.g. 'SECOND DAY'.

    Only the text is kept, so headings with the same text are equal. That is
    how marshalling.py finds the same heading on two papers.
    """

    text: str


class Amendment:
    def __init__(self, amdt: _Element, parent_doc: 'SupDocument'):
        self.parent_doc = parent_doc
        _num = amdt.find(
            'amendment/amendmentBody/amendmentContent/tblock/num', namespaces=NSMAP2
        )
        _xml = amdt.find('amendment/amendmentBody', namespaces=NSMAP2)
        self._names: list[str] | None = None
        self.star = Star(amdt.get(QName(UKL, 'statusIndicator'), default=''))

        if _num is not None and _num.text and _xml is not None:
            self.num: str = _num.text
            self.xml: _Element = _xml
            # LawMaker's own reference for the amendment (e.g. HoC72, OPC275).
            # Only used for display at the moment, e.g. to tell apart
            # amendments that wrongly share a number. Not used for matching.
            self.dnum: str = _num.get(QName(UKL, 'dnum'), default='')
        else:
            logger.warning(f'{_num=}, {_xml=}')
            raise ValueError(
                'amendmentBody or amendmentBody/amendmentContent/tblock/num is None'
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

    @cached_property
    def description(self) -> str:
        """
        A short description of the amendment, e.g. for the side-by-side
        order in the Check Amendment Papers report:
        - A new clause or schedule: its heading, e.g. 'Application of CIL to
          householders'.
        - Any other amendment: its instruction, without the text it would
          insert, up to the first '—', e.g. 'Clause 12, page 8, line 5, at
          end insert'.
        - An amendment to an amendment starts with what it amends, e.g.
          'To NC10: Line 10, at end insert'.

        Returns '' if the amendment has no instruction.
        """

        instruction = self.xml.find(
            'amendmentContent/tblock/block[@name="instruction"]', namespaces=NSMAP2
        )
        if instruction is None:
            return ''

        description = ''

        if self.xml.get(QName(UKL, 'type'), '') in ('newClause', 'newSchedule'):
            # the heading of the new clause or schedule, e.g.
            # <quotedStructure><section><num/><heading>...
            heading = instruction.find('.//quotedStructure/*/heading', NSMAP2)
            if heading is not None:
                description = ''.join(heading.itertext())

        if not description.strip():
            description = _text_outside_quotes(instruction).split('—')[0]

        description = ' '.join(description.split())

        # e.g. ukl:targetProvision="amnd_NC10" on an amendment to NC10
        target = self.xml.get(QName(UKL, 'targetProvision'), '')
        if target.startswith('amnd_'):
            description = f'To {target.removeprefix("amnd_")}: {description}'

        return description


def _text_outside_quotes(element: _Element) -> str:
    """
    The text of element, leaving out any quoted structures (the text that an
    amendment would insert). Comments and processing instructions are left
    out too.
    """

    parts = [element.text or '']

    for child in element:
        if isinstance(child.tag, str) and child.tag != f'{{{XMLNS}}}quotedStructure':
            parts.append(_text_outside_quotes(child))
        parts.append(child.tail or '')

    return ''.join(parts)


class SupDocument(Mapping):
    """Container for an amendment document aka official list"""

    def __init__(self, xml: Path | _Element):
        if isinstance(xml, Path):
            self.file_name = xml.name
            self.file_path = str(xml.resolve())
            tree = etree.parse(self.file_path, parser=PARSER)
            self.root = tree.getroot()
        else:
            self.file_name = 'Test'
            self.file_path = 'test/Test'
            tree = etree.ElementTree(xml)
            self.root = xml

        self.short_file_name = truncate_string(self.file_name).replace('.xml', '')

        # build up metadata
        self.meta_list_type: str
        self.meta_bill_title: str
        self.meta_pub_date: str
        self.meta_house: str  # e.g. 'House of Commons'
        self.meta_stage: str  # e.g. 'Report Stage'

        # The names of any metadata not found, e.g. ['Bill Title']. A value
        # that is not found is set to a warning message to show in reports,
        # so check this list before comparing values between papers.
        self.missing_meta: list[MetadataName] = []

        self.get_meta_data()

        self.problem_amendments = 0
        self.amendments: list[Amendment] = []

        # The amendments and headings, in paper order. Orders of the House
        # and programme motions are left out: they come after the amendments.
        # Amendments that cannot be read are left out, as in self.amendments.
        self.sequence: list[Amendment | Heading] = []

        # for amdt_xml in xp.get_amendments(self.root):
        #     try:
        #         amendment = Amendment(amdt_xml, self)
        #         self.amendments.append(amendment)
        #     except ValueError as e:
        #         logger.warning(repr(e))
        #         self.problem_amendments += 1

        for component in xp.get_amendments_and_headings(self.root):
            if component.get('class') == 'heading':
                # all the text, with runs of spaces and line breaks made
                # into single spaces, e.g. 'FIRST DAY ' becomes 'FIRST DAY'
                text = ' '.join(xp.text_content(component).split())
                if text:
                    self.sequence.append(Heading(text))
                else:
                    logger.info(f'{self.file_name} has an empty heading. Ignoring it.')
                continue

            try:
                amendment = Amendment(component, self)
                self.amendments.append(amendment)
                self.sequence.append(amendment)
            except ValueError as e:
                logger.warning(repr(e))
                self.problem_amendments += 1

        # amendment number -> every amendment with that number, for numbers
        # used more than once. Filled in by _create_amdt_map.
        self.duplicate_nums: dict[str, list[Amendment]] = {}
        self._dict: dict[str, Amendment] = self._create_amdt_map()
        self.amdt_set = set(self._dict.keys())

    def get_meta_data(self):

        self.meta_list_type = self._get_metadata_display(
            ".//xmlns:block[@name='listType']/text()", 'List Type'
        )

        self.meta_bill_title = self._get_metadata_display(
            ".//xmlns:TLCConcept[@eId='varBillTitle']/@showAs", 'Bill Title'
        )

        try:
            # TODO consider using self._get_metadata_display here too
            # add a test for this
            published_date = self.root.find(
                ".//FRBRManifestation/FRBRdate[@name='published']", namespaces=NSMAP2
            )
            # sometimes published date include the time info
            # e.g. 2023-09-06T00:00:00Z
            # so we need to strip that out
            _published_date = published_date.get('date', default='')
            if _published_date:
                # remove the time info
                _published_date = _published_date.split('T')[0]
            else:
                _published_date = ''
            self.meta_pub_date = datetime.strptime(
                _published_date,  # type: ignore
                '%Y-%m-%d',
            ).strftime('%A %d %B %Y')

        except Exception as e:
            warning_msg = f"Can't find Published Date meta data. Check {self.file_name}"
            self.meta_pub_date = warning_msg
            self.missing_meta.append('Published Date')
            if not isinstance(e, AttributeError):
                warning_msg += f': {repr(e)}'
            logger.info(f'Problem parsing XML. {warning_msg}')

        # Amendment numbers start again at each stage, so reports that
        # compare two papers use these to check the papers are from the same
        self.meta_house = self._get_metadata_display(
            ".//xmlns:TLCConcept[@eId='varHouse']/@showAs", 'House'
        )
        self.meta_stage = self._get_metadata_display(
            ".//xmlns:TLCProcess[@eId='varStageVersion']/@showAs", 'Stage'
        )

    def _get_metadata_display(self, xpath: str, name: MetadataName) -> str:
        """
        Extract metadata value from the element found by xpath.

        xpath should select the text or attribute directly, e.g.
        ".//xmlns:block[@name='listType']/text()" or
        ".//xmlns:TLCConcept[@eId='varHouse']/@showAs"
        Use the xmlns: prefix: without it nothing matches

        If nothing is found (or it is empty), add name to self.missing_meta,
        log it at INFO and return a warning message to show instead. Reports
        that need the value (e.g. check_papers_match) give their own warning.
        """

        results = self.root.xpath(xpath, namespaces=NSMAP)
        value = results[0].strip() if results and isinstance(results[0], str) else ''

        if not value:
            warning_msg = f"Can't find {name} meta data. Check {self.file_name}"
            self.missing_meta.append(name)
            logger.info(f'Problem parsing XML. {warning_msg}')
            return warning_msg

        return value

    def _create_amdt_map(self) -> dict[str, Amendment]:
        """
        Map each amendment number to its amendment.

        Amendment numbers should be unique. If several amendments share a
        number, only the first (in document order) goes in the map, so a
        report that looks amendments up by number will only see that one.
        All of them are recorded in self.duplicate_nums so that reports can
        warn about it, and all of them are still in self.amendments.
        """

        _amdt_map: dict[str, Amendment] = {}

        for amendment in self.amendments:
            if amendment.num in _amdt_map:
                first = _amdt_map[amendment.num]
                self.duplicate_nums.setdefault(amendment.num, [first])
                self.duplicate_nums[amendment.num].append(amendment)
                continue
            _amdt_map[amendment.num] = amendment

        for num, amendments in self.duplicate_nums.items():
            logger.warning(
                f'{self.file_name} has {len(amendments)} amendments numbered'
                f' {num}. Amendment numbers should be unique!'
            )

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
