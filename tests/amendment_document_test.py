from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from lxml.etree import ElementTree

import data_for_testing
from lawchecker.amendment_document import Amendment, Heading, SupDocument
from lawchecker.settings import NSMAP2
from paper_builder import make_amendment, make_heading, make_paper

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


# ------------------- Sequence (amendments and headings) ----------------- #


def numbers_and_headings(sup_doc: SupDocument) -> list[str | Heading]:
    """The sequence, with each amendment shown as its number"""

    return [
        item.num if isinstance(item, Amendment) else item for item in sup_doc.sequence
    ]


def test_sequence():
    sup_doc = SupDocument(
        make_paper(
            make_heading('FIRST DAY'),
            make_heading('NEW CLAUSES'),
            make_amendment('NC1'),
            make_amendment('1'),
            make_heading('SECOND DAY'),
            make_amendment('2'),
        )
    )

    assert numbers_and_headings(sup_doc) == [
        Heading('FIRST DAY'),
        Heading('NEW CLAUSES'),
        'NC1',
        '1',
        Heading('SECOND DAY'),
        '2',
    ]

    # the amendments in the sequence are the ones in sup_doc.amendments
    amendments = [item for item in sup_doc.sequence if isinstance(item, Amendment)]
    assert amendments == sup_doc.amendments


def test_heading_spaces_tidied():
    sup_doc = SupDocument(make_paper(make_heading('  FIRST\n    DAY ')))

    assert sup_doc.sequence == [Heading('FIRST DAY')]


def test_heading_in_two_parts():
    """
    A heading can be split over two <i> elements, as in Health 0902. Real
    papers also have line breaks and indents between the elements.
    """

    heading = """
    <component class="heading">
     <interstitial>
      <block name="heading"><i>CLAUSES 1 TO 61, </i><i>THE NHS</i></block>
     </interstitial>
    </component>
    """
    sup_doc = SupDocument(make_paper(heading))

    assert sup_doc.sequence == [Heading('CLAUSES 1 TO 61, THE NHS')]


def test_empty_heading_left_out(caplog):
    sup_doc = SupDocument(
        make_paper(make_heading(''), make_amendment('1'), make_heading('  '))
    )

    assert numbers_and_headings(sup_doc) == ['1']
    assert caplog.text.count('Test has an empty heading. Ignoring it.') == 2


def test_unreadable_amendment_left_out_of_sequence():
    """An amendment with no number is left out, as in sup_doc.amendments"""

    sup_doc = SupDocument(
        make_paper(make_amendment('1'), make_amendment(''), make_amendment('2'))
    )

    assert numbers_and_headings(sup_doc) == ['1', '2']
    assert sup_doc.problem_amendments == 1


def test_duplicate_numbers_in_sequence():
    """Both amendments are in the sequence, in paper order"""

    sup_doc = SupDocument(
        make_paper(
            make_amendment('NC52', dnum='HoC1'),
            make_amendment('NC53', dnum='HoC2'),
            make_amendment('NC52', dnum='HoC3'),
        )
    )

    assert [item.dnum for item in sup_doc.sequence if isinstance(item, Amendment)] == [
        'HoC1',
        'HoC2',
        'HoC3',
    ]


# the number of headings on each example paper (none on the others)
HEADINGS_ON = {
    'english_dev_rm_rep_1119.xml': 4,
    'health_rm_rep_0902.xml': 4,
    'health_rm_rep_0903.xml': 4,
    'health_rm_rep_0904.xml': 4,
    'health_day_rep_0907.xml': 4,
    'health_day_rep_0908.xml': 2,
}


@pytest.mark.parametrize(
    'path', sorted(EXAMPLES.glob('*.xml')), ids=lambda path: path.name
)
def test_sequence_real_papers(path: Path):
    sup_doc = SupDocument(path)

    amendments = [item for item in sup_doc.sequence if isinstance(item, Amendment)]
    headings = [item for item in sup_doc.sequence if isinstance(item, Heading)]

    assert amendments == sup_doc.amendments
    assert len(headings) == HEADINGS_ON.get(path.name, 0)


def test_headings_real_paper():
    sup_doc = SupDocument(EXAMPLES / 'health_rm_rep_0902.xml')

    headings = [
        (i, item.text)
        for i, item in enumerate(sup_doc.sequence)
        if isinstance(item, Heading)
    ]

    assert headings == [
        (0, 'FIRST DAY'),
        (
            1,
            'NEW CLAUSES AND NEW SCHEDULES RELATING TO THE SUBJECT MATTER OF, AND'
            ' AMENDMENTS TO, CLAUSES 1 TO 61 AND SCHEDULES 1 TO 8, NEW CLAUSES AND'
            ' NEW SCHEDULES RELATING TO WOMEN’S HEALTH, MATERNITY, PROCUREMENT AND'
            ' TRADE, AND THE WORKFORCE OF THE NHS',
        ),
        (133, 'SECOND DAY'),
        (
            134,
            'NEW CLAUSES AND NEW SCHEDULES RELATING TO THE SUBJECT MATTER OF, AND'
            ' AMENDMENTS TO, CLAUSES 62 TO 81 AND SCHEDULES 9 TO 12, REMAINING NEW'
            ' CLAUSES AND NEW SCHEDULES; REMAINING PROCEEDINGS ON CONSIDERATION',
        ),
    ]
