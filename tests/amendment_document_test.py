from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from lxml.etree import ElementTree

import data_for_testing
from lawchecker.amendment_document import SupDocument
from lawchecker.settings import NSMAP2
from paper_builder import make_amendment, make_paper

# built from this file's location so the tests work from any directory
EXAMPLES = Path(__file__).resolve().parent.parent / 'example_files' / 'amendments'

# ---------------------------- Metadata ---------------------------------- #


def test_meta_data_extract():
    with patch('lxml.etree.parse') as mock_parse:
        mock_parse.return_value = ElementTree(data_for_testing.intro_input)

        sup_doc = SupDocument(Path('test'))

        assert sup_doc.meta_list_type == '(Amendment Paper)'
        assert sup_doc.meta_bill_title == 'Energy Bill [HL]'
        assert sup_doc.meta_pub_date == 'Monday 04 September 2023'


def test_get_meta_data():
    """Test the case with no bill title attribute"""

    with patch('lxml.etree.parse') as mock_parse:
        element = deepcopy(data_for_testing.intro_input)
        tlcconcept = element.find(
            ".//TLCConcept[@eId='varBillTitle']", namespaces=NSMAP2
        )

        # remove the bill title attribute
        tlcconcept.attrib.clear()  # type: ignore

        mock_parse.return_value = ElementTree(element)

        sup_doc = SupDocument(Path('test'))

        warning_msg = "Can't find Bill Title meta data. Check test"
        assert sup_doc.meta_bill_title == warning_msg


def test_house_and_stage():
    sup_doc = SupDocument(EXAMPLES / 'english_dev_rm_pbc_1010.xml')

    assert sup_doc.meta_house == 'House of Commons'
    assert sup_doc.meta_stage == 'Committee Stage'
    assert sup_doc.missing_meta == []


def test_missing_meta():
    """Metadata that is not found is listed, and shown as a warning message"""

    sup_doc = SupDocument(make_paper(stage=''))

    assert sup_doc.missing_meta == [
        'List Type',
        'Bill Title',
        'Published Date',
        'House',
        'Stage',
    ]
    assert sup_doc.meta_house == "Can't find House meta data. Check Test"
    assert sup_doc.meta_stage == "Can't find Stage meta data. Check Test"


# ---------------------- Duplicate amendment numbers --------------------- #


def test_duplicate_amendment_numbers_are_recorded(caplog):
    """No amendment is dropped, and the duplicates are recorded"""

    sup_doc = SupDocument(
        make_paper(
            make_amendment('NC52', dnum='HoC1'),
            make_amendment('NC52', dnum='HoC2'),
        )
    )

    # both amendments are kept in the list...
    assert len(sup_doc.amendments) == 2
    first, second = sup_doc.amendments
    assert [first.dnum, second.dnum] == ['HoC1', 'HoC2']

    # ...but there is only one entry per number, and it is the first one
    assert len(sup_doc) == 1
    assert sup_doc['NC52'] is first

    assert sup_doc.duplicate_nums == {'NC52': [first, second]}
    assert 'Test has 2 amendments numbered NC52' in caplog.text


def test_no_duplicate_amendment_numbers():
    sup_doc = SupDocument(make_paper(make_amendment('NC52'), make_amendment('NC53')))

    assert sup_doc.duplicate_nums == {}
    assert list(sup_doc) == ['NC52', 'NC53']
