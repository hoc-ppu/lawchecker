"""
Build small LawMaker amendment papers for tests.

A test states only the details that matter to it, for example:

    paper = make_paper(
        make_amendment('NC52', star='★'),
        make_amendment('NC53', dnum='HoC2', proposer='Bob Example'),
    )

Everything else gets a default. The XML is the minimum that SupDocument and
the reports need. It is not a complete LawMaker paper, so the reports will
log warnings about missing metadata (bill title, published date and so on).
"""

from xml.sax.saxutils import escape, quoteattr

from lxml import etree
from lxml.etree import _Element

from lawchecker.stars import Star

XMLNS = 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
UKL = 'https://www.legislation.gov.uk/namespaces/UK-AKN'


def make_amendment(
    num: str,
    *,
    star: str | Star | None = None,
    dnum: str = '',
    proposer: str | None = 'Ann Example',
    supporters: tuple[str, ...] = (),
    instruction: str = 'Clause 1, page 1, line 1, leave out “example”',
) -> str:
    """
    Return the XML for one amendment (a <component>), as a string.

    star: '★', '☆', or None for no star (the attribute is left out, as in
        real papers). Star objects (e.g. BLACK_STAR) also work. Any other
        string is written as it is, for testing bad values in the XML.
    proposer: None gives an amendment with no sponsors at all.
    """

    if isinstance(star, Star):
        star = None if star.is_no_star else str(star)

    star_attr = '' if star is None else f' ukl:statusIndicator={quoteattr(star)}'

    names = ''
    if proposer is not None:
        names += (
            '<block name="proposer">'
            f'<docIntroducer refersTo="">{escape(proposer)}</docIntroducer>'
            '</block>'
        )
    if supporters:
        names += (
            '<block name="supporters">'
            + ''.join(
                f'<docProponent refersTo="">{escape(name)}</docProponent>'
                for name in supporters
            )
            + '</block>'
        )

    return (
        f'<component class="amendment"{star_attr}>'
        '<amendment name="hcamnd">'
        '<amendmentBody>'
        f'<amendmentHeading>{names}</amendmentHeading>'
        '<amendmentContent><tblock>'
        f'<num ukl:dnum={quoteattr(dnum)}>{escape(num)}</num>'
        f'<block name="instruction">{escape(instruction)}</block>'
        '</tblock></amendmentContent>'
        '</amendmentBody>'
        '</amendment>'
        '</component>'
    )


def make_paper(*amendments: str) -> _Element:
    """Return an amendment paper containing the given amendments, in order."""

    return etree.fromstring(
        f'<akomaNtoso xmlns="{XMLNS}" xmlns:ukl="{UKL}">'
        '<amendmentList><collectionBody>'
        f'{"".join(amendments)}'
        '</collectionBody></amendmentList>'
        '</akomaNtoso>'
    )
