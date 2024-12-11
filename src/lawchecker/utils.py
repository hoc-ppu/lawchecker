import difflib
import re

from lxml import etree
from lxml.etree import Element, QName, _Element

from lawchecker.lawchecker_logger import logger
from lawchecker import xpath_helpers as xp


def is_line_junk(line: str) -> bool:
    """
    Return True if line is considered junk, False otherwise.
    """

    return line.isspace() or line.strip() == ""


# html diff object
html_diff = difflib.HtmlDiff(tabsize=6)
# html_diff = difflib.HtmlDiff(tabsize=6, linejunk=is_line_junk)


nbsp = re.compile(r"(?<!&nbsp;)&nbsp;(?!</span>)(?!&nbsp;)")


def remove_refs(parent_element: _Element) -> _Element:
    """
    Remove ref elements from parent_element and all its descendant elements.
    Note: parent_element is modified in place.
    """

    for element in parent_element.iter(Element):
        tag = QName(element).localname
        if tag == "ref":
            try:
                element.getparent().remove(element)  # type: ignore
            except Exception as e:
                logger.warning(f"Error removing ref element: {e}")

    return parent_element



def clean_whitespace(parent_element: _Element) -> _Element:

    """
    Remove unwanted whitespace from parent_element and all its descendant
    elements. Note: parent_element is modified in place.
    Add a newline after parent_elements (which represent paragraphs)
    """

    # these are inline elements, we should leave them well alone
    # I think defined here:
    # https://docs.oasis-open.org/legaldocml/akn-core/v1.0/cos01/part2-specs/schemas/akomantoso30.xsd
    # //xsd:schema/xsd:group[@name="HTMLinline"]/xsd:choice
    # plus ref and def which are also inline
    inlines = (
        "b", "i", "a", "u", "sub", "sup", "abbr", "span",
        "ref", "rref", "mref", "def"
    )

    # paragraph elements. Add new line after.
    paragraphs = ("p", "docIntroducer", "docProponent", "heading",)  # "mod"?


    for element in parent_element.iter(Element):
        tag = QName(element).localname

        if tag == "inline" and element.get("name") == "AppendText" and element.text:
            element.text = f"{element.text} "

        if tag in inlines:
            continue

        # remove whitespace
        if element.text:
            element.text = element.text.lstrip()
        if element.tail:
            element.tail = element.tail.strip()

        is_block_instruction = tag == "block" and element.get("name") == "instruction"

        if tag in paragraphs or is_block_instruction:
            # Add in newlines after each of these elements
            try:
                last_child = element[-1]
            except IndexError:
                last_child = None

            if last_child is not None:
                # print(f"{tag=}, {last_child=}")
                # add test for this.
                if last_child.tail:
                    last_child.tail = f"{last_child.tail}\n"
                else:
                    last_child.tail = "\n"
                # print(f"{last_child.tail=}")
            elif element.text:
                element.text = f"{element.text.rstrip()}\n"
            if element.tail and not element.tail.isspace():
                # occasionally paragraph elements have tail text. for instance in tables
                # e.g. see Leasehold and Freehold Reform Bill from about January 2024
                element.tail = f"{element.tail}\n"

            # print(f"{etree.tostring(element).decode()}\n")

        if tag == "mod" and element.text:
            # TODO: improve this. See Terrorism (Protection of Premises)  2R & AAC. Session 2024-25
            element.text = f"{element.text}\n"

        if tag == "quotedStructure" and element.getprevious() is not None:
            previous: _Element = element.getprevious()  # type: ignore
            if previous.tail and previous.tail.endswith("—"):
                previous.tail = f"{previous.tail}\n"
            elif previous.text and previous.text.endswith("—"):
                previous.text = f"{previous.text}\n"

        if tag == "num" and element.text:
            # Add in space after num element
            element.text = f"{element.text} "

    return parent_element


def diff_xml_content(
    new_xml: _Element,
    old_xml: _Element,
    fromdesc: str = "",
    todesc: str = "",
    ignore_refs: bool = False,
) -> str | None:
    """
    Return an HTML string containing a tables showing the differences
    between old_xml and new_xml.
    """

    # remove the unnecessary whitespace before comparing the text content
    cleaned_old_xml = clean_whitespace(old_xml)
    cleaned_new_xml = clean_whitespace(new_xml)

    if ignore_refs:
        # when ignore refs is True, remove refs from the xml
        # then compare the text content
        # return none if no changes (when refs are removed)
        old_text_content_no_refs = xp.text_content(remove_refs(cleaned_old_xml))
        new_text_content_no_refs = xp.text_content(remove_refs(cleaned_new_xml))

        if new_text_content_no_refs == old_text_content_no_refs:
            # no changes
            return

    old_text_content = xp.text_content(cleaned_old_xml)
    new_text_content = xp.text_content(cleaned_new_xml)

    if new_text_content == old_text_content:
        # no changes
        return
    else:
        # if only the first number has changed e.g. clause number we can ignore
        # test this on amendment papers too.
        no_num_new_text_content = re.sub(r"^\d+\s", "", new_text_content)
        no_num_old_text_content = re.sub(r"^\d+\s", "", old_text_content)

        if no_num_new_text_content == no_num_old_text_content:
            return


    fromlines = old_text_content.splitlines()
    tolines = new_text_content.splitlines()

    # fromlines = [line.strip() for line in fromlines if line.strip()]
    # tolines = [line.strip() for line in tolines if line.strip()]

    dif_html_str = html_diff.make_table(
        fromlines,
        tolines,
        fromdesc=fromdesc,
        todesc=todesc,
        context=True,
        numlines=3,
    )
    dif_html_str = dif_html_str.replace('nowrap="nowrap"', "")

    # remove nbsp but only when not in a span (as spans are used for changes
    # e.g. <span class="diff_sub">) and not if this nbsp is folowed by
    # another nbsp (as this is used for indentation)
    dif_html_str = nbsp.sub(" ", dif_html_str)

    return dif_html_str
