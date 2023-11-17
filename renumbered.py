import logging
import re
from pathlib import Path

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

    for file in xml_files:
        print(file)
        xml = etree.parse(str(file))
        root = xml.getroot()

        # get the sections
        sections = get_sections(root)

        print(get_version(root))


def get_sections(xml_element: _Element):

    # body element
    body = xml_element.find('.//xmlns:body', namespaces=NSMAP)

    if body is None:
        logger.error("No body element!")
        return


    attrs = []
    para_attrs = []

    sections = body.xpath("//xmlns:section", namespaces=NSMAP)

    for section in sections:

        guid = section.get('GUID', None)
        eid = section.get('eId', None)

        if guid is None or eid is None:
            logger.warning("Section with no GUID or EID")
            continue

        # skip subsections, qstr elements
        if "subsec" in eid or "qstr" in eid:
            continue

        # and oc notations (duplicated)
        # I think here we are supposed to edit the eid value to remove '__' and anything after it
        try:
            eid = eid.split("__")[0]
        except IndexError:
            pass


        attrs.append([guid, eid])

    paragraphs = body.xpath("//xmlns:paragraph", namespaces=NSMAP)

    for paragraph in paragraphs:

        guid = paragraph.get('GUID', None)
        eid = paragraph.get('eId', None)

        if guid is None or eid is None:
            logger.warning("Section with no GUID or EID")
            continue

        # only keep the schedules
        if "sched" not in eid:
            continue

        # remove subpara and qstr (duplicated)
        if "subpara" in eid or "qstr" in eid:
            continue

        # remove oc notations (__oc_#, sometimes at end and sometimes middle of string)
        eid = re.sub(r"__oc_\d+", "", eid)

        para_attrs.append([guid, eid])

    # print(para_attrs)
    print(len(para_attrs))


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
