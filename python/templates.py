from copy import deepcopy
from typing import Iterable, Optional, cast

from lxml import etree, html
from lxml.etree import _Element, iselement

_card = html.fromstring("""<section class="card">
<div class="card-inner collapsible">
  <div class="collapsible-header">
    <h2><span class="arrow"> </span>--headers go here--</h2>
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
</section>""")

_table = html.fromstring('<table class="sticky-head table-responsive-md table">'
                         '<thead></thead><tbody></tbody>'
                         '</table>')

_table_row = html.fromstring('<tr></tr>')

_collapsable_section = html.fromstring("""<section class="collapsible closed">
  <div class="collapsible-header">
    <h3><span class="arrow"> </span>Name Changes in Context</h3>
  </div>
  <div class="collapsible-content" style="display: none;">
  </div>
</section>""")


class Card:
    def __init__(self, heading: str = ""):
        self.html = deepcopy(_card)
        heading_span = self.html.find('.//h2/span[@class="arrow"]')
        self.heading_span = cast(_Element, heading_span)
        secondary_info = self.html.find('.//div[@class="secondary-info"]')
        self.secondary_info = cast(_Element, secondary_info)
        tertiary_info = self.html.find('.//div[@class="info-inner"]')
        self.tertiary_info = cast(_Element, tertiary_info)

        if (
            self.heading_span is None
            or self.secondary_info is None
            or self.tertiary_info is None
        ):
            raise ValueError("_card has invalid structure")
        else:
            self.heading_span.tail = heading


    # return card


class Table:
    def __init__(self, table_headings: Iterable[str]):

        self.html = deepcopy(_table)

        self.table_head = cast(_Element, self.html.find('.//thead'))
        self.table_body = cast(_Element, self.html.find('.//tbody'))

        if table_headings:
            self.table_head.append(html.fromstring(
                '<tr><th scope="col">' + '</th><th scope="col">'.join(table_headings) + '</th></tr>'
            ))

    def add_row(self, row: Iterable[str]):

        """Add a row to the table.
        Row should be an iterable of strings, one for each cell in the row.
        The strings should be a plain text or HTML representing the contents of the cell."""

        row_element = deepcopy(_table_row)
        row_element.extend((html.fromstring(f'<td>{cell}</td>') for cell in row))
        self.table_body.append(row_element)


class CollapsableSection:
    def __init__(self, heading: str = ""):
        self.html = deepcopy(_collapsable_section)
        self.heading_span = self.html.find('.//h3/span[@class="arrow"]')
        self.collapsible_content = self.html.find('.//div[@class="collapsible-content"]')

        if (
            self.heading_span is None
            or self.collapsible_content is None
        ):
            raise ValueError("_collapsable_section has invalid structure")
        else:
            self.heading_span.tail = heading

    def add_content(self, content: Optional[str] = None, content_element: Optional[etree.ElementBase] = None):
        if content is not None:
            self.collapsible_content.append(html.fromstring(content))
        elif content_element is not None:
            if iselement(content_element):
                self.collapsible_content.append(content_element)
            else:
                raise ValueError("content_element is not a valid lxml element")
        else:
            raise ValueError("Must provide either content or content_element")

    # def add_table(self, table: Table):
    #     self.collapsible_content.append(table.html)

    # def add_card(self, card: Card):
    #     self.collapsible_content.append(card.html)