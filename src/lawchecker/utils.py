import difflib
import re
from copy import deepcopy
from typing import Sequence

from lxml import etree
from lxml.etree import Element, QName, _Element, iselement

from lawchecker import xpath_helpers as xp
from lawchecker.compare_bill_numbering import NSMAP
from lawchecker.lawchecker_logger import logger


def truncate_string(s, max_length=26):
    """
    Truncate a string to a maximum length by replacing the middle
    characters with three dots.

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

    return line.isspace() or line.strip() == ''


# html diff object
html_diff = difflib.HtmlDiff(tabsize=6)
# html_diff = difflib.HtmlDiff(tabsize=6, linejunk=is_line_junk)


nbsp = re.compile(r'(?<!&nbsp;)&nbsp;(?!</span>)(?!&nbsp;)')


def drop_tag(element: _Element) -> None:
    """
    Remove the tag, but not its children or text.  The children and text
    are merged into the parent.

    Example::

        >>> h = fragment_fromstring('<div>Hello <b>World!</b></div>')
        >>> h.find('.//b').drop_tag()
        >>> print(tostring(h, encoding='unicode'))
        <div>Hello World!</div>
    """
    parent = element.getparent()
    assert parent is not None
    previous = element.getprevious()
    if element.text and isinstance(element.tag, str):
        # not a Comment, etc.
        if previous is None:
            parent.text = (parent.text or '') + element.text
        else:
            previous.tail = (previous.tail or '') + element.text
    if element.tail:
        if len(element):
            last = element[-1]
            last.tail = (last.tail or '') + element.tail
        elif previous is None:
            parent.text = (parent.text or '') + element.tail
        else:
            previous.tail = (previous.tail or '') + element.tail
    index = parent.index(element)
    parent[index : index + 1] = element[:]


def remove_refs(parent_element: _Element) -> _Element:
    """
    Remove ref elements from parent_element and all its descendant elements.
    """

    # Create a copy of the parent element
    # we will remove references only from the copy so that the
    # original parent element is not modified this is because
    # sometimes the cross references are taken out in LM but the
    # text that was within in the ref element is left behind if
    # we don't do this, and remove the ref element from the original
    # when comparing the text content of the two elements, we will get
    # a difference where there is none
    parent_copy = deepcopy(parent_element)

    for element in parent_copy.iter(Element):
        tag = QName(element).localname
        if tag == 'ref':
            try:
                element.getparent().remove(element)  # type: ignore
            except Exception as e:
                logger.warning(f'Error removing ref element: {e}')

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

    # I don't think the <inline> element is included... strangely...
    inlines = (
        'b',
        'i',
        'a',
        'u',
        'sub',
        'sup',
        'abbr',
        'span',
        'ref',
        'rref',
        'mref',
        'def',
    )

    return tag in inlines


def drop_inline_elements(parent_element: _Element) -> _Element:
    """
    Remove inline elements from parent_element and all its descendant elements.
    """

    # Create a copy of the parent element
    # we will remove inline elements only from the copy so that the
    # original parent element is not modified
    parent_copy = deepcopy(parent_element)

    for element in parent_copy.iter(Element):
        tag = QName(element).localname
        if is_inline_element(tag):
            drop_tag(element)

    return parent_copy


def clean_json_html_amdt(parent_element: _Element) -> _Element:
    """ "
    Add a newline after p elements
    """

    # TODO: do we need this function at all?

    parent_copy = deepcopy(parent_element)

    for element in parent_copy.iter(Element):
        tag = QName(element).localname

        if tag == 'p':
            # Add in newlines after each of these elements
            try:
                last_child = element[-1]
            except IndexError:
                last_child = None

            if last_child is not None:
                # add test for this.
                if last_child.tail and not last_child.tail.endswith('\n'):
                    last_child.tail = f'{last_child.tail}\n'
                else:
                    last_child.tail = '\n'
            elif element.text:
                element.text = f'{element.text.rstrip()}\n'
            if (
                element.tail
                and not element.tail.isspace()
                and not element.tail.endswith('\n')
            ):
                # occasionally paragraph elements have tail text. for instance in tables
                # e.g. see Leasehold and Freehold Reform Bill from about January 2024
                element.tail = f'{element.tail}\n'

    return parent_copy


def clean_lm_xml_amdt(parent_element: _Element) -> _Element:
    """
    Remove unwanted whitespace from parent_element and all its descendant
    elements. Add a newline after elements (which represent paragraphs)
    """

    parent_copy = drop_inline_elements(parent_element)

    # paragraph elements. Add new line after.
    paragraphs = (
        'p',
        'docIntroducer',
        'docProponent',
        'heading',
    )  # "mod"?

    for element in parent_copy.iter(Element):
        tag = QName(element).localname

        parent: Element | None = element.getparent()
        parent_tag = ''
        if parent is not None:
            parent_tag = QName(parent).localname

        if tag == 'inline' and element.get('name') == 'AppendText' and element.text:
            no_following_sibling = element.getnext() is None

            parent_is_mod = parent_tag == 'mod'

            logger.info(f'inline element with text: {element.text}')
            # logger.info(f'{parent_is_mod=}, {no_following_sibling=} {parent=}')
            if no_following_sibling and parent_is_mod:
                # AppendText at end of mod element. Add newline
                element.text = f'{element.text}\n'
                logger.info('Added newline to AppendText inline element')
            else:
                element.text = f'{element.text} '

        # if is_inline_element(tag):
        #     continue

        # remove some leading and trailing spaces
        if element.text:
            element.text = element.text.lstrip()
        if element.tail:
            element.tail = element.tail.strip()

        is_special_block = tag == 'block' and element.get('name') in (
            'instruction',
            'withdrawn',
        )

        if tag in paragraphs or is_special_block:
            # Add in newlines after each of these elements
            try:
                last_child = element[-1]
            except IndexError:
                last_child = None

            if last_child is not None:
                # add test for this.
                if last_child.tail and not last_child.tail.endswith('\n'):
                    last_child.tail = f'{last_child.tail}\n'
                else:
                    last_child.tail = '\n'
            elif element.text:
                element.text = f'{element.text.rstrip()}\n'
            if (
                element.tail
                and not element.tail.isspace()
                and not element.tail.endswith('\n')
            ):
                # occasionally paragraph elements have tail text. for instance in tables
                # e.g. see Leasehold and Freehold Reform Bill from about January 2024
                element.tail = f'{element.tail}\n'

        if tag == 'mod' and element.text:
            # TODO: improve this.
            # See Terrorism (Protection of Premises)  2R & AAC. Session 2024-25
            element.text = f'{element.text}\n'

        if tag == 'quotedStructure' and element.getprevious() is not None:
            previous: _Element = element.getprevious()  # type: ignore
            if previous.tail and previous.tail.endswith('—'):
                previous.tail = f'{previous.tail}\n'
            elif previous.text and previous.text.endswith('—'):
                previous.text = f'{previous.text}\n'

        if tag == 'num' and element.text:
            if parent_tag == 'part':
                element.text = f'{element.text}\n'
            else:
                # Add in space after num element
                element.text = f'{element.text} '
            # if '(1)' in element.text:
            #     logger.info('Found number one')
            #     logger.info(etree.tostring(element))

    return parent_copy


def diff_xml_content(
    new_xml: _Element,
    old_xml: _Element,
    fromdesc: str = '',
    todesc: str = '',
    ignore_refs: bool = False,
) -> str | None:
    """
    Return an HTML string containing a tables showing the differences
    between old_xml and new_xml.
    """

    # remove the unnecessary whitespace before comparing the text content
    cleaned_old_xml = clean_lm_xml_amdt(old_xml)
    cleaned_new_xml = clean_lm_xml_amdt(new_xml)

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
        no_num_new_text_content = re.sub(r'^\d+\s', '', new_text_content)
        no_num_old_text_content = re.sub(r'^\d+\s', '', old_text_content)

        if no_num_new_text_content == no_num_old_text_content:
            return

    fromlines = old_text_content.splitlines()
    tolines = new_text_content.splitlines()

    # fromlines = [line.strip() for line in fromlines if line.strip()]
    # tolines = [line.strip() for line in tolines if line.strip()]

    dif_html_str = html_diff_lines(
        fromlines,
        tolines,
        fromdesc=fromdesc,
        todesc=todesc,
    )

    # dif_html_str = html_diff.make_table(
    #     fromlines,
    #     tolines,
    #     fromdesc=fromdesc,
    #     todesc=todesc,
    #     context=True,
    #     numlines=3,
    # )
    # dif_html_str = dif_html_str.replace('nowrap="nowrap"', "")

    # # remove nbsp but only when not in a span (as spans are used for changes
    # # e.g. <span class="diff_sub">) and not if this nbsp is folowed by
    # # another nbsp (as this is used for indentation)
    # dif_html_str = nbsp.sub(" ", dif_html_str)

    return dif_html_str


def fix_consecutive_quotes(text: str) -> str:
    """
    Fix cases where consecutive quotation marks have unwanted newlines between them.
    """
    text = re.sub(r'\n(?=[”"])', '', text)
    return text


def html_diff_lines(
    fromlines: Sequence[str],
    tolines: Sequence[str],
    fromdesc: str = '',
    todesc: str = '',
    context=True,
    numlines=2,
) -> str | None:
    fromlines = [normalise_spaces(line) for line in fromlines if line.strip()]
    tolines = [normalise_spaces(line) for line in tolines if line.strip()]

    if fromlines == tolines:
        return None

    dif_html_str = html_diff.make_table(
        fromlines,
        tolines,
        fromdesc=fromdesc,
        todesc=todesc,
        context=context,
        numlines=numlines,
    )
    dif_html_str = dif_html_str.replace('nowrap="nowrap"', '')

    # remove nbsp but only when not in a span (as spans are used for changes
    # e.g. <span class="diff_sub">) and not if this nbsp is folowed by
    # another nbsp (as this is used for indentation)
    dif_html_str = nbsp.sub(' ', dif_html_str)

    return dif_html_str


def normalise_text(text: str) -> str:
    return normalise_new_lines(normalise_spaces(text))


def normalise_new_lines(text: str) -> str:
    """
    Normalize newline placement in text for consistent formatting.

    Adjusts newlines around quotation marks, em dashes, and semicolons to improve
    text comparison. Adds newlines after closing quotes and em dashes, removes
    newlines before opening quotes and after semicolons, collapses consecutive
    newlines, and strips leading/trailing whitespace.

    Args:
        text: The text string to normalize.

    Returns:
        The text with normalized newline placement.
    """
    text = text.replace('”', '”\n')
    text = text.replace('\n”', '”')
    text = text.replace('“\n', '“')

    # definition lists often start with two opening quote characters
    text = text.replace('““', '\n““')

    # not worried about newlines after semi-colons
    text = text.replace(';\n', '; ')

    # let's add a new line after an em dash
    text = text.replace('—', '—\n')

    text = re.sub(r'\n\n+', '\n', text)

    text = '\n'.join(line.strip() for line in text.splitlines())

    text = text.strip()

    return text


def normalise_spaces(text: str) -> str:
    """
    Normalize whitespace and special characters within text lines.

    Removes spaces around quotation marks and em dashes, replaces non-breaking
    spaces and figure spaces with regular spaces, collapses multiple consecutive
    spaces into single spaces, and strips leading/trailing whitespace.

    Args:
        text: The text string to normalize.

    Returns:
        The normalized text string.
    """

    text = re.sub(r' +”', '”', text)
    text = re.sub(r'“ +', '“', text)

    # I have decided that I don't care about spaces around em dashes
    text = re.sub(r' +— +', '—', text)
    # text = text.replace('— ', '—')

    text = text.replace('\u00a0', ' ')  # non-breaking space
    text = text.replace('\u2007', ' ')  # figure space
    text = text.replace('\u2009', ' ')  # Thin space
    text = text.replace('\u200a', ' ')  # Hair space
    text = text.replace('\u202f', ' ')  # Narrow no-break space
    text = text.replace('\u2003', ' ')  # Em space
    text = text.replace('\u2002', ' ')  # En space
    text = text.replace('\u200b', ' ')  # Zero-width space
    text = text.replace('\t', ' ')

    text = re.sub(r'[^\S\n][^\S\n]+', ' ', text)

    text = text.strip()

    return text


def clean_amendment_number(amendment_number: str) -> str:
    """
    Cleans the amendment number by removing brackets.
    """
    # remove brackets and spaces
    amendment_number = amendment_number.replace('(', '').replace(')', '').strip()

    return amendment_number


def get_stage_from_amdts_xml(amdt_xml_root: _Element) -> str | None:
    """
    Get the stage from the amendment XML.

    Try a couple of different methods to find the stage.
    """

    try:
        # block = amdt_xml_root.xpath('//*[local-name()="block"][@name="stage"]')
        stage = xp.text_content(
            amdt_xml_root.xpath(
                '//xmlns:block[@name="stage"]/xmlns:docStage', namespaces=NSMAP
            )[0]
        )
        return stage
    except Exception as e:
        logger.info('Using alternative way to find stage in amendment XML')
        try:
            stage = amdt_xml_root.xpath(
                '//xmlns:TLCProcess[@eId="varStageVersion"][1]/@showAs',
                namespaces=NSMAP,
            )[0]

            logger.info(f'Found stage using alternative method: {stage}')
            return stage
        except Exception as e:
            logger.warning(repr(e))
            return None
