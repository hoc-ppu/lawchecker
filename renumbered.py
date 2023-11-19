import logging
import re
from pathlib import Path

import pandas as pd
from lxml import etree
from lxml.etree import _Element

NSMAP = {
    "xmlns": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
}


# BEGIN LOGGER
logger = logging.getLogger('renumbered')

ch = logging.StreamHandler()  # create console handler
ch.setLevel(logging.WARNING)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to the handler(s)
ch.setFormatter(formatter)

logger.addHandler(ch)  # add the handler to the logger
# END LOGGER


def main():

    # get all the XML files in the current directory
    xml_files = Path(".").glob("*.xml")

    data = []

    for file in xml_files:
        print(file)
        xml = etree.parse(str(file))
        root = xml.getroot()

        # get the sections
        data.append(get_sections(root))

        print(get_version(root))

    data_frames = [pd.DataFrame(d) for d in data]

    if len(data_frames) == 2:
        # data_frames[0].join(data_frames[1], how="left", on="guid")
        df = data_frames[0].set_index('guid').join(data_frames[1].set_index('guid'), how="outer")
        df.to_csv("data.csv")


def get_sections(root: _Element):

    attrs = {"eid": [], "guid": []}

    xpath = (
        "//xmlns:body//xmlns:section"          # sections
        "[not(contains(@eId, 'subsec')) "      # skip subsections
        "and not(contains(@eId, 'qstr'))]"     # skip qstr elements
        "|//xmlns:body//xmlns:paragraph"       # paragraphs
        "[contains(@eId, 'sched') "            # only keep the schedules
        "and not(contains(@eId, 'subpara')) "  # remove subpara
        "and not(contains(@eId, 'qstr'))]"     # and qstr (duplicated)
    )

    sections_paragraphs: list[_Element] = root.xpath(xpath, namespaces=NSMAP)  # type: ignore

    if len(sections_paragraphs) == 0:
        logger.warning("No sections or paragraphs found")
        return attrs

    for element in sections_paragraphs:

        guid = element.get('GUID', None)
        eid = element.get('eId', None)

        if guid is None or eid is None:
            logger.warning("Section with no GUID or EID")
            continue

        element_name = etree.QName(element).localname

        if element_name == "section":

            # and oc notations (duplicated)
            # I think here we are supposed to edit the eid value to remove '__' and anything after it
            try:
                eid = eid.split("__")[0]
            except IndexError:
                pass

        if element_name == "paragraph":

            # remove oc notations (__oc_#, sometimes at end and sometimes middle of string)
            eid = re.sub(r"__oc_\d+", "", eid)

        attrs["eid"].append(eid)
        attrs["guid"].append(guid)

    return attrs


def get_version(xml_root: _Element) -> str:

    xpath_temp = '//xmlns:references/*[@eId="{}"]/@showAs'
    stage_xp = xpath_temp.format("varStageVersion")
    house_xp = xpath_temp.format("varHouse")

    stage: str = xml_root.xpath(stage_xp, namespaces=NSMAP)[0]  # type: ignore
    house: str = xml_root.xpath(house_xp, namespaces=NSMAP)[0]  # type: ignore

    house = house.replace("House of ", "")

    return f"{house}, {stage}"


if __name__ == "__main__":
    main()
