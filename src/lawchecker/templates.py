from copy import deepcopy
from typing import Iterable, Optional, Sequence, cast

from lxml import etree, html
from lxml.etree import iselement
from lxml.html import HtmlElement

_card = html.fromstring("""<section class="card">
<div class="card-inner collapsible">
  <div class="collapsible-header">
    <h2><span class="arrow"> </span>--headers go here--<small class="text-muted"> [hide]</small></h2>
  </div>
  <div class="collapsible-content">
    <div class="content">
      <div class="secondary-info">
      <!-- This is where secondary info goes -->
      </div>
    </div>
    <div class="info">
      <div class="info-inner">
        <!-- Tertiary info -->
      </div>
    </div>
  </div>
</div>
</section>
""")

_table = html.fromstring(
    '<table class="sticky-head table-responsive-md table"><thead></thead><tbody></tbody></table>'
)

_table_row = html.fromstring('<tr></tr>')

_collapsable_section = html.fromstring("""<section class="collapsible closed">
  <div class="collapsible-header">
    <h3><span class="arrow"> </span>Name Changes in Context</h3>
  </div>
  <div class="collapsible-content" style="display: none;">
  </div>
</section>""")


_small_collapsable_section = html.fromstring("""<div class="collapsible collapsible-small closed">
  <div class="collapsible-header collapsible-small">
    <p><span class="arrow"> </span></p>
  </div>
  <p class="collapsible-content" style="display: none;">
  </p>
</div>""")

_names_change_context_section = html.fromstring(
    '<section class="collapsible closed">'
    '<div class="collapsible-header">'
    '<h3 class="h4"><span class="arrow"> </span>'
    'Name Changes in Context <small class="text-muted"> [show]</small></h3>'
    '<p>Expand this section to see the same names as above but in context.</p>'
    '</div>'
    '<div class="collapsible-content" style="display: none;" id="name-changes-in-context">'
    '</div>'
    '</section>'
)

basic_document = html.fromstring(
    '<html><head><meta charset="utf-8">'
    '<style>'
    'body {font-family: system-ui, "Segoe UI", "Helvetica Neue", Arial, sans-serif;}'
    '.editableBox {border: 1px solid #ccc; padding: 10px; margin: 20px;}'
    '.editableBox p {margin-top: 0.25rem; margin-bottom: 0.25rem;}'
    '</style></head>'
    '<body><main class="main" id="main-content"></main></body></html>'
)

editable_text_div = html.fromstring(
    '<div class="editableBox" contenteditable="true"></div>'
    # '<div class="editableBox"></div>'
)


class Counter:
    def __init__(self):
        self.count = 0  # Initialize the counter at 0

    def increment(self):
        self.count += 1  # Increment the counter by 1
        return self.count


counter = Counter()


class Card:
    def __init__(self, heading: str = '', expanded: bool = True):
        self.html = deepcopy(_card)
        heading_element = self.html.find('.//h2')
        self.heading_element = cast(HtmlElement, heading_element)
        heading_span = self.html.find('.//h2/span[@class="arrow"]')
        self.heading_span = cast(HtmlElement, heading_span)
        secondary_info = self.html.find('.//div[@class="secondary-info"]')
        self.secondary_info = cast(HtmlElement, secondary_info)
        tertiary_info = self.html.find('.//div[@class="info-inner"]')
        self.tertiary_info = cast(HtmlElement, tertiary_info)
        small = self.html.find('.//h2/small')
        self.small = cast(HtmlElement, small)
        collapsible_content = self.html.find('.//div[@class="collapsible-content"]')
        self.collapsible_content = cast(HtmlElement, collapsible_content)

        if (
            self.heading_span is None
            or heading_element is None
            or self.secondary_info is None
            or self.tertiary_info is None
            or self.small is None
            or self.collapsible_content is None
        ):
            raise ValueError('_card has invalid structure')
        else:
            self.heading_span.tail = heading  # type: ignore
            self.heading_element.set('data-heading-label', heading)
            self.heading_element.set('id', f'card-{counter.increment()}')

        if expanded:
            # content should start expanded
            self.small.text = ' [hide]'  # type: ignore
        else:
            self.small.text = ' [show]'  # type: ignore
            self.collapsible_content.set('style', 'display: none;')

    # return card


class Table:
    def __init__(
        self,
        table_headings: Iterable[str],
        table_rows: Iterable[Iterable[str | HtmlElement]] = [],
    ):
        self.html = deepcopy(_table)

        self.table_head = cast(HtmlElement, self.html.find('.//thead'))
        self.table_body = cast(HtmlElement, self.html.find('.//tbody'))

        if table_headings:
            self.table_head.append(
                html.fromstring(
                    '<tr><th scope="col">'
                    + '</th><th scope="col">'.join(table_headings)
                    + '</th></tr>'
                )
            )

        if table_rows:
            for row in table_rows:
                self.add_row(row)

    def add_row(self, row: Iterable[str | HtmlElement]):
        """Add a row to the table.
        Row should be an iterable of strings, one for each cell in the row.
        The strings should be a plain text or HTML representing the contents of the cell."""

        row_element = deepcopy(_table_row)
        for cell in row:
            if isinstance(cell, str):
                row_element.append(html.fromstring(f'<td>{cell}</td>'))
            elif iselement(cell):
                if cell.tag == 'td':
                    row_element.append(cell)
                else:
                    td = html.fromstring('<td></td>')
                    td.append(cell)
                    row_element.append(td)
            else:
                raise TypeError('Row must contain only strings or lxml elements')

        # row_element.extend((html.fromstring(f'<td>{cell}</td>') for cell in row))
        self.table_body.append(row_element)


class CollapsableSection:
    def __init__(self, heading: str = ''):
        self.html = deepcopy(_collapsable_section)
        self.heading_span = self.html.find('.//h3/span[@class="arrow"]')
        self.collapsible_content = self.html.find(
            './/div[@class="collapsible-content"]'
        )

        if self.heading_span is None or self.collapsible_content is None:
            raise ValueError('_collapsable_section has invalid structure')
        else:
            self.heading_span.tail = heading

    def add_content(
        self,
        content: Optional[str] = None,
        content_element: Optional[etree.ElementBase] = None,
    ):
        if content is not None:
            self.collapsible_content.append(html.fromstring(content))  # type: ignore
        elif content_element is not None:
            if iselement(content_element):
                self.collapsible_content.append(content_element)  # type: ignore
            else:
                raise ValueError('content_element is not a valid lxml element')
        else:
            raise ValueError('Must provide either content or content_element')

    # def add_table(self, table: Table):
    #     self.collapsible_content.append(table.html)

    # def add_card(self, card: Card):
    #     self.collapsible_content.append(card.html)


class NameChangeContextSection:
    def __init__(self):
        self.html = deepcopy(_names_change_context_section)

        content_xpath = ".//div[@id='name-changes-in-context']"
        self.content: HtmlElement = self.html.find(content_xpath)  # type: ignore

        if self.content is None:
            raise ValueError('_names_change_context_section has invalid structure')

    def add_content(self, content_elements: Sequence[HtmlElement]):
        self.content.extend(content_elements)

    def clear(self):
        self.html = html.Element('div')


class SmallCollapsableSection:
    def __init__(self, heading: str | HtmlElement = ''):
        self.html = deepcopy(_small_collapsable_section)

        span_xpath = './div/p[span]'
        self.heading_e: HtmlElement = self.html.find(span_xpath)  # type: ignore

        content_xpath = './p[@class="collapsible-content"]'
        self.collapsible: HtmlElement = self.html.find(content_xpath)  # type: ignore

        if self.heading_e is None or self.collapsible is None:
            raise ValueError('_small_collapsable_section has invalid structure')

        if isinstance(heading, str):
            self.heading_e.append(html.fromstring(heading))
        else:
            self.heading_e.append(heading)


class EditableTextDiv:
    def __init__(self, content: str = '', children: Sequence[HtmlElement] = []):
        self.html = deepcopy(editable_text_div)
        if content:
            self.html.text = content

        self.html.extend(children)

    def set_content(self, content: str):
        self.html.text = content
