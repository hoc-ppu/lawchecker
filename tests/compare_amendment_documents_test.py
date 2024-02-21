import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import data_for_testing
import pytest
from lxml import etree
from lxml.etree import ElementTree, _Element

# the below line is only needed if you don't pip install the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lawchecker import compare_amendment_documents as compare
from lawchecker.settings import NSMAP2
from lawchecker.stars import BLACK_STAR, NO_STAR, WHITE_STAR


@pytest.fixture
def report() -> compare.Report:
    report = compare.Report(
        Path("example_files/amendments/energy_rm_rep_0904.xml").resolve(),
        Path("example_files/amendments/energy_day_rep_0905.xml").resolve(),
    )

    return report


def _elements_equal(e1, e2, ignore_whitespace=True):
    if e1.tag != e2.tag:
        return False
    if e1.attrib != e2.attrib:
        return False
    if ignore_whitespace:
        if e1.text and e2.text and e1.text.strip() != e2.text.strip():
            return False
        if e1.tail and e2.tail and e1.tail != e2.tail:
            return False
    else:
        if e1.text != e2.text:
            return False
        if e1.tail != e2.tail:
            return False
    if len(e1) != len(e2):
        return False

    # true when both have no children empty
    return all(_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

def assert_elements_equal(e1: _Element, e2: _Element, ignore_whitespace=True):

    """By comparing the strings we get better error messages when elements are not equal"""

    if _elements_equal(e1, e2, ignore_whitespace):
        # return True
        assert True
    else:

        # indent elements in place
        etree.indent(e1, space=" ")
        etree.indent(e2, space=" ")

        e1_string = etree.tostring(e1, encoding="utf-8")
        e2_string = etree.tostring(e2, encoding="utf-8")

        # return e1_string == e2_string
        assert e1_string == e2_string

# def to


def test_diff_names_in_context_warning(caplog):

    """
    Test that warning is generated when there is a problem finding sponsors
    """

    doc_skeleton = deepcopy(data_for_testing.intro_input)

    # skeleton has no amendments so we will use this:
    amdt = deepcopy(data_for_testing.dummy_amendment_with_white_star)

    # edit amendment to remove the sponsors
    amdt.find(".//amendmentHeading", namespaces=NSMAP2).clear()

    # put the skeleton and the amendment together
    doc_skeleton.find(
        ".//amendmentList", namespaces=NSMAP2
    ).extend(  # type: ignore
        amdt.find(".//amendmentList", namespaces=NSMAP2)  # type: ignore
    )

    compare.Report(
        doc_skeleton,
        doc_skeleton,
    )

    assert "NC52: no sponsors found" in caplog.text


def test_render_intro(report):
    """Test that the intro is rendered correctly"""

    assert_elements_equal(data_for_testing.intro, report.render_intro())


def test_added_and_removed_names_table(report):
    """Test that the added and removed names are rendered correctly"""

    assert_elements_equal(
        data_for_testing.added_and_removed_names_table, report.added_and_removed_names_table()
    )


def test_meta_data_extract():
    with patch("lxml.etree.parse") as mock_parse:
        mock_parse.return_value = ElementTree(data_for_testing.intro_input)

        sup_doc = compare.SupDocument(Path("test"))

        assert sup_doc.meta_list_type == "(Amendment Paper)"
        assert sup_doc.meta_bill_title == "Energy Bill [HL]"
        assert sup_doc.meta_pub_date == "Monday 04 September 2023"


def test_get_meta_data():

    """Test the case with no bill title attribute"""

    with patch("lxml.etree.parse") as mock_parse:
        element = deepcopy(data_for_testing.intro_input)
        tlcconcept = element.find(
            ".//TLCConcept[@eId='varBillTitle']", namespaces=compare.NSMAP2
        )

        # remove the bill title attribute
        tlcconcept.attrib.clear()  # type: ignore

        mock_parse.return_value = ElementTree(element)

        sup_doc = compare.SupDocument(Path("test"))

        warning_msg = "Can't find Bill Title meta data. Check test"
        assert sup_doc.meta_bill_title == warning_msg


# ----------------- Test star check is done properly ----------------- #

def test_black_star_to_white():

    """Test case where black stars change to white stars"""

    # this is a correct case

    white_star_amend = deepcopy(data_for_testing.dummy_amendment_with_white_star)
    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)

    report = compare.Report(black_star_amend, white_star_amend)
    assert report.correct_stars == [f"NC52 ({WHITE_STAR})"]


def test_white_star_to_no_star():

    """Test case where white stars change to no star"""

    # this is a correct case

    white_star_amend = deepcopy(data_for_testing.dummy_amendment_with_white_star)
    no_star_amend = deepcopy(data_for_testing.dummy_amendment_with_no_star)

    report = compare.Report(white_star_amend, no_star_amend)
    assert report.correct_stars == [f"NC52 ({NO_STAR})"]


def test_black_star_to_black():
    """test case where black stars are not updated"""

    # this is an incorrect case. Items with black stars
    # should have white stars on their second appearance.

    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)
    black_star_amend2 = deepcopy(black_star_amend)

    report = compare.Report(black_star_amend, black_star_amend2)
    assert report.incorrect_stars == [f"NC52 has {BLACK_STAR} ({WHITE_STAR} expected)"]


def test_white_star_to_white_star():
    """test case where white star not updated"""

    # this is an incorrect case. Items with a white star
    # should have no star on their next (3rd) appearance

    white_star_amend = deepcopy(data_for_testing.dummy_amendment_with_white_star)
    white_star_amend2 = deepcopy(white_star_amend)

    report = compare.Report(white_star_amend, white_star_amend2)
    assert report.incorrect_stars == [f"NC52 has {WHITE_STAR} ({NO_STAR} expected)"]


def test_white_star_to_black_star():

    """test case where white star changes to black star"""

    # this is an incorrect case. Items with a white star
    # should have no star on their next (3rd) appearance.
    # A black star here is likely a mistake

    white_star_amend = deepcopy(data_for_testing.dummy_amendment_with_white_star)
    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)

    report = compare.Report(white_star_amend, black_star_amend)
    assert report.incorrect_stars == [f"NC52 has {BLACK_STAR} ({NO_STAR} expected)"]


def test_black_star_to_no_star():

    """test case where a black star changes to no star"""

    # this is an incorrect case. Likely a mistake.

    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)
    no_star_amend = deepcopy(data_for_testing.dummy_amendment_with_no_star)

    report = compare.Report(black_star_amend, no_star_amend)
    assert report.incorrect_stars == [f"NC52 has {NO_STAR} ({WHITE_STAR} expected)"]


def test_unknown_star_attribute_in_xml_new_item():

    """test case where the star attribute is not one of the three expected values
    in the new amendment"""

    # this is an incorrect case. Likely a mistake.

    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)
    unknown_star_amend = deepcopy(data_for_testing.dummy_amendment_with_unknown_star)

    report = compare.Report(black_star_amend, unknown_star_amend)
    assert report.incorrect_stars == [f"NC52 has Error with star ({WHITE_STAR} expected)"]


def test_unknown_star_attribute_in_xml_old_item():

    """test case where the star attribute is not one of the three expected values
    in the old amendment"""

    # this is an incorrect case. Likely a mistake.

    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)
    unknown_star_amend = deepcopy(data_for_testing.dummy_amendment_with_unknown_star)

    report = compare.Report(unknown_star_amend, black_star_amend)
    assert report.incorrect_stars == ['Error with star in Test, NC52 check manually.']


def test_black_star_to_no_star_when_days_between():

    """when there are sitting days between the two documents being compared
    all stars become no stars"""

    black_star_amend = deepcopy(data_for_testing.dummy_amendment_with_black_star)
    no_star_amend = deepcopy(data_for_testing.dummy_amendment_with_no_star)

    report = compare.Report(black_star_amend, no_star_amend, days_between_papers=True)
    assert report.correct_stars == [f"NC52 ({NO_STAR})"]
