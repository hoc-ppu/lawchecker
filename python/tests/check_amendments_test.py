import os
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from lxml import etree
from lxml.etree import ElementTree, _Element

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print(str(Path(__file__).resolve().parent.parent))

import check_amendments
import data_for_testing


@pytest.fixture
def report() -> check_amendments.Report:
    report = check_amendments.Report(
        Path("LM_XML/energy_rm_rep_0904.xml").resolve(),
        Path("LM_XML/energy_day_rep_0905.xml").resolve(),
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

def elements_equal(e1: _Element, e2: _Element, ignore_whitespace=True):

    """By comparing the strings we get better error messages when elements are not equal"""

    if _elements_equal(e1, e2, ignore_whitespace):
        return True
    else:
        e1_string = etree.tostring(etree.indent(e1, space="  "))
        e2_string = etree.tostring(etree.indent(e2, space="  "))
        return e1_string == e2_string



def test_render_intro(report):
    """Test that the intro is rendered correctly"""

    assert elements_equal(data_for_testing.intro, report.render_intro()) is True


def test_added_and_removed_names_table(report):
    """Test that the added and removed names are rendered correctly"""

    assert elements_equal(
        data_for_testing.added_and_removed_names_table, report.added_and_removed_names_table()
    ) is True


def test_meta_data_extract():
    with patch("lxml.etree.parse") as mock_parse:
        mock_parse.return_value = ElementTree(data_for_testing.intro_input)

        sup_doc = check_amendments.SupDocument(Path("test"))

        assert sup_doc.meta_list_type == "(Amendment Paper)"
        assert sup_doc.meta_bill_title == "Energy Bill [HL]"
        assert sup_doc.meta_pub_date == "Monday 04 September 2023"


def test_get_meta_data():

    """Test the case with no bill title attribute"""

    with patch("lxml.etree.parse") as mock_parse:
        element = deepcopy(data_for_testing.intro_input)
        tlcconcept = element.find(
            ".//TLCConcept[@eId='varBillTitle']", namespaces=check_amendments.NSMAP2
        )

        # remove the bill title attribute
        tlcconcept.attrib.clear()  # type: ignore

        mock_parse.return_value = ElementTree(element)

        sup_doc = check_amendments.SupDocument(Path("test"))

        warning_msg = "Can't find Bill Title meta data. Check test"
        assert sup_doc.meta_bill_title == warning_msg


def test_black_star_to_white():

    """Test case where black stars change to white stars"""

    # this is a correct case

    white_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_white_star)
    black_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_black_star)

    report = check_amendments.Report(black_star_amend, white_star_amend)
    assert report.correct_stars == ["NC52 (☆)"]


def test_white_star_to_no_star():

    """Test case where white stars change to no star"""

    # this is a correct case

    white_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_white_star)
    no_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_no_star)

    report = check_amendments.Report(white_star_amend, no_star_amend)
    assert report.correct_stars == ["NC52 (no star)"]


def test_black_star_to_black():
    """test case where black stars are not updated"""

    # this is an incorrect case. Items with black stars
    # should have white stars on their second appearance.

    black_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_black_star)
    black_star_amend2 = deepcopy(black_star_amend)

    report = check_amendments.Report(black_star_amend, black_star_amend2)
    assert report.incorrect_stars == ["NC52 has black star (White star expected)"]

def test_white_star_to_white_star():
    """test case where white star not updated"""

    # this is an incorrect case. Items with a white star
    # should have no star on their next (3rd) appearance

    white_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_white_star)
    white_star_amend2 = deepcopy(white_star_amend)

    report = check_amendments.Report(white_star_amend, white_star_amend2)
    assert report.incorrect_stars == ["NC52 has white star (No star expected)"]

def test_white_star_to_black_star():

    """test case where white star changes to black star"""

    # this is an incorrect case. Items with a white star
    # should have no star on their next (3rd) appearance.
    # A black star here is likely a mistake

    white_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_white_star)
    black_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_black_star)

    report = check_amendments.Report(white_star_amend, black_star_amend)
    assert report.incorrect_stars == ["NC52 has black star (No star expected)"]

def test_black_star_to_no_star():

    """test case where a black star changes to no star"""

    # this is an incorrect case. Likely a mistake.

    black_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_black_star)
    no_star_amend = etree.fromstring(data_for_testing.dummy_amendment_with_no_star)

    report = check_amendments.Report(black_star_amend, no_star_amend)
    assert report.incorrect_stars == ["NC52 has no star (White star expected)"]


