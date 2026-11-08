#!/usr/bin/env python3

"""
Shared container classes for a LawMaker XML official list document (amendment
paper) and the individual amendments within it.

These are used by both compare_amendment_documents.py and
duplicate_amendments.py.
"""

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from lxml import etree
from lxml.etree import QName, _Element

from lawchecker import xpath_helpers as xp
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import NSMAP2, PARSER, UKL
from lawchecker.stars import Star
from lawchecker.utils import truncate_string


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

        # amendment number -> every amendment with that number, for numbers
        # used more than once. Filled in by _create_amdt_map.
        self.duplicate_nums: dict[str, list[Amendment]] = {}
        self._dict: dict[str, Amendment] = self._create_amdt_map()
        self.amdt_set = set(self._dict.keys())

    def get_meta_data(self):
        try:
            list_type = self.root.find(".//block[@name='listType']", namespaces=NSMAP2)
            self.meta_list_type = list_type.text  # type: ignore
        except Exception as e:
            warning_msg = f"Can't find List Type meta data. Check {self.file_name}"
            self.meta_list_type = warning_msg
            logger.warning(f'Problem parsing XML. {warning_msg}: {repr(e)}')

        try:
            bill_title = self.root.find(
                ".//TLCConcept[@eId='varBillTitle']", namespaces=NSMAP2
            )
            # don't use .get here  as that defaults to None
            self.meta_bill_title = bill_title.attrib['showAs']  # type: ignore
            # [x] test
        except Exception as e:
            warning_msg = f"Can't find Bill Title meta data. Check {self.file_name}"
            self.meta_bill_title = warning_msg
            logger.warning(f'Problem parsing XML. {warning_msg}: {repr(e)}')

        try:
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
            if not isinstance(e, AttributeError):
                warning_msg += f': {repr(e)}'
            logger.info(f'Problem parsing XML. {warning_msg}')

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
