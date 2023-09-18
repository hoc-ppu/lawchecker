import os
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from lxml.etree import ElementTree

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
print(str(Path(__file__).resolve().parent.parent))

import data_for_testing

import check_amendments


@pytest.fixture
def report() -> check_amendments.Report:
    report = check_amendments.Report(
        Path("LM_XML/energy_rm_rep_0904.xml").resolve(),
        Path("LM_XML/energy_day_rep_0905.xml").resolve(),
    )

    return report


def elements_equal(e1, e2, ignore_whitespace=True):
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
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


def test_render_intro(report):
    """Test that the intro is rendered correctly"""

    assert elements_equal(data_for_testing.intro, report.render_intro()) is True


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
        tlcconcept.attrib.clear()  # remove the bill title attribute

        mock_parse.return_value = ElementTree(element)

        sup_doc = check_amendments.SupDocument(Path("test"))

        warning_msg = "Can't find Bill Title meta data. Check test"
        assert sup_doc.meta_bill_title == warning_msg
