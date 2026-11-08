"""
Test data that the paper builder (paper_builder.py) does not cover.

intro_input is a paper with metadata but no amendments, used by the
metadata tests in amendment_document_test.py.
"""

from lxml import etree

# flake8: noqa

intro_input = etree.fromstring(
"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:ukl="https://www.legislation.gov.uk/namespaces/UK-AKN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://docs.oasis-open.org/legaldocml/ns/akn/3.0 ../schemas/akomantoso30.xsd">
<?LDAPP-Component componentId="" ?>
	<amendmentList contains="originalVersion" name="hcmarsh">
	 <meta>
	  <identification source="#source">

	   <!-- good -->
	   <FRBRManifestation>
		<FRBRdate date="2023-09-04" name="published"/>
	   </FRBRManifestation>
	   <!-- g -->
	  </identification>
	  <references source="#author">

		<!-- good -->
	   <TLCConcept eId="varBillTitle" href="#varOntologies" showAs="Energy Bill [HL]"/>
	   <!-- g -->

	   <TLCProcess eId="varStageVersion" href="#varOntologies" showAs="Report Stage"/>

	  </references>
	 </meta>
	 <preface eId="preface">
		<!-- good -->
		<block name="listType">(Amendment Paper)</block>
		<!-- g -->
	 </preface>
	</amendmentList>
</akomaNtoso>"""
)
