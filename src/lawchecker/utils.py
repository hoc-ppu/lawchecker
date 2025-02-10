import difflib
import re
from copy import deepcopy

from lxml.etree import Element, QName, _Element

from lawchecker import xpath_helpers as xp
from lawchecker.lawchecker_logger import logger


def truncate_string(s, max_length=26):

    """
    Truncate a string to a maximum length by replacing the middle characters with three dots.

    If the string length is greater than the specified maximum length, the
    middle characters are replaced with '__'. The resulting string will have
    the specified maximum length.
    """

    if len(s) <= max_length:
        return s
    else:
        # Calculate the number of characters to keep on each side
        keep_length = (max_length - 2) // 2
        return s[:keep_length] + '__' + s[-keep_length:]


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
    """

    # Create a copy of the parent element
    # we will remove references only from the copy
    # so that the original parent element is not modified
    # this is because sometimes the cross references are taken out
    # but the text that was within in the ref element is left behind
    # if we don't do this, and remove the ref element from the original
    # when comparing the text content of the two elements, we will get
    # a difference where there is none
    parent_copy = deepcopy(parent_element)

    for element in parent_copy.iter(Element):
        tag = QName(element).localname
        if tag == "ref":
            try:
                element.getparent().remove(element)  # type: ignore
            except Exception as e:
                logger.warning(f"Error removing ref element: {e}")

    return parent_copy


def is_inline_element(tag: str) -> bool:
    """
    Return True if element is an inline element, False otherwise.
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

    return tag in inlines


def clean_whitespace(parent_element: _Element) -> _Element:

    """
    Remove unwanted whitespace from parent_element and all its descendant
    elements. Add a newline after parent_elements (which represent paragraphs)
    """

    parent_copy = deepcopy(parent_element)

    # paragraph elements. Add new line after.
    paragraphs = ("p", "docIntroducer", "docProponent", "heading",)  # "mod"?

    for element in parent_copy.iter(Element):
        tag = QName(element).localname

        if tag == "inline" and element.get("name") == "AppendText" and element.text:
            element.text = f"{element.text} "

        if is_inline_element(tag):
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
                # add test for this.
                if last_child.tail and not last_child.tail.endswith("\n"):
                    last_child.tail = f"{last_child.tail}\n"
                else:
                    last_child.tail = "\n"
            elif element.text:
                element.text = f"{element.text.rstrip()}\n"
            if element.tail and not element.tail.isspace() and not element.tail.endswith("\n"):
                # occasionally paragraph elements have tail text. for instance in tables
                # e.g. see Leasehold and Freehold Reform Bill from about January 2024
                element.tail = f"{element.tail}\n"

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

    return parent_copy


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
