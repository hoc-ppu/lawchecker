"""
Wrappers for some common XML processing tasks. This module relies on lxml:
https://pypi.org/project/lxml/
https://lxml.de/
"""

from lxml import etree

from lawchecker.lawchecker_logger import logger


def load_xml(input_file_path: str) -> etree._ElementTree | None:
    """
    Load an XML document from `input_file_path`.
    """

    logger.info(f"Loading XML from <{input_file_path}>...")

    return_value = None

    try:

        xml_document = etree.parse(input_file_path, parser=None)

        if type(xml_document) is etree._ElementTree:

            return_value = xml_document

            logger.info(f"XML loaded from <{input_file_path}>")

    except TypeError:

        logger.error("`load_xml` expects `input_file_path` to be a string.")

    except OSError:

        logger.error(f"`load_xml` could not read file <{input_file_path}>.")

    except etree.XMLSyntaxError:

        logger.error(f"<{input_file_path}> is not a valid XML file.")

    return return_value


def validate_xml(
    xml_document: etree._ElementTree, xsd_document: etree._ElementTree
) -> bool:

    # log info

    return_value = False

    # TODO validate xml_document against xsd_document

    # if valid
    #     return_value = True
    #     log success

    # else
    #     log error

    return return_value


def transform_xml(
    input_xml_document: etree._ElementTree, xsl_document: etree._ElementTree
) -> etree._XSLTResultTree | None:
    """
    Transform XML using XSLT and return the result.
    """

    logger.info("Transforming XML with XSLT...")

    return_value = None

    try:

        transform = etree.XSLT(xsl_document)

        output_xml_document = transform(input_xml_document)

        if type(output_xml_document) is etree._XSLTResultTree:

            return_value = output_xml_document

            logger.info("XML transformed.")

    except (etree.XSLTParseError):

        logger.error("There was a problem transforming the XML.")

    return return_value
