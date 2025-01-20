import glob
import os
import re
import sys
import traceback

import requests
from lxml import etree as ET
from lxml.etree import iselement

from lawchecker.lawchecker_logger import logger

# TODO: Add logging
# Run Black on this file


def get_marshal_xml(folder_path):
    """Load additional XML files for checking amendments."""
    marshal_files = []

    # Get all XML files in the folder
    xml_files = glob.glob(os.path.join(folder_path, "*.xml"))

    if not xml_files:
        logger.info(f"No XML files found in the folder: {folder_path}")
        return marshal_files

    for file_path in xml_files:
        try:
            tree = ET.parse(file_path)
            marshal_files.append(tree)
            logger.info(f"Loaded XML file: {file_path}")
        except ET.XMLSyntaxError as e:
            logger.error(f"Failed to parse XML file at {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while loading {file_path}: {e}")

    return marshal_files

def fetch_eligible_members():

    """Returns the member names from MNIS API for name checking."""

    # TODO: cache the response for a certain period of time

    url = "https://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons|IsEligible=true/"
    response = requests.get(url)
    if response.status_code == 200:
        members_tree = ET.fromstring(response.content)
        # Extract <DisplayAs> text for each <Member> in the API response
        return {
            member.find("DisplayAs").text  # TODO: would it be better to use .findtext()?
            for member in members_tree.findall(".//Member")
            if member.find("DisplayAs") is not None
        }
    else:
        print("Failed to fetch data from MNIS API.")
        return set()

def check_amendment_in_files(amendment_num, bill_title, marshal_files):
    """
    Matches an amendment number and bill title in the provided checking files.
    """
    for file_tree in marshal_files:
        namespaces = {k if k else "default": v for k, v in file_tree.getroot().nsmap.items()}
        tlc_query = f"//*[local-name()='TLCConcept' and @eId='varBillTitle'][@showAs='{bill_title}']"
        amendments_query = f"//*[local-name()='num' and @ukl:dnum='{amendment_num}']"

        tlc_elements = file_tree.xpath(tlc_query, namespaces=namespaces)
        if tlc_elements:
            amendment_elements = file_tree.xpath(amendments_query, namespaces=namespaces)
            if amendment_elements:
                logger.debug(f"Found amendment '{amendment_num}' in bill '{bill_title}'")
                return True
            else:
                logger.debug(f"Amendment '{amendment_num}' not found for bill '{bill_title}' in checking XML.")
        else:
            logger.debug(f"Bill '{bill_title}' not found in checking XML.")
    return False

def reorder_amendments(marshal_files, bill_title, amendment_groups):
    """
    Reorder amendment groups based on checking XML files with debugging.
    """
    ordered_amendment_groups = []
    remaining_amendments = amendment_groups.copy()
    was_reordered = False  # Track if any reordering occurred

    for checking_file in marshal_files:
        root = checking_file.getroot()
        namespaces = {
            'akn': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0',
            'ukl': 'https://www.legislation.gov.uk/namespaces/UK-AKN'
        }

        # Match bill-title
        bill_title_match = root.xpath(".//akn:TLCConcept[@eId='varBillTitle']/@showAs", namespaces=namespaces)
        if not bill_title_match:
            logger.debug(f"No bill-title found in {checking_file.docinfo.URL}")
            continue

        if bill_title_match[0] != bill_title:
            logger.debug(f"Bill title '{bill_title}' does not match '{bill_title_match[0]}' in {checking_file.docinfo.URL}")
            continue

        logger.debug(f"Matched Bill Title: {bill_title_match[0]} in {checking_file.docinfo.URL}")

        all_nums = root.xpath(".//akn:num[@ukl:dnum]", namespaces={
        "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
        "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"
        })
        logger.debug(f"Found {len(all_nums)} <num> elements in the XML.")
        for num in all_nums:
            logger.debug(f"<num>: {ET.tostring(num, pretty_print=True, encoding='unicode')}".strip())

        # Extract amendment order from checking file
        amendment_order = root.xpath(".//akn:num[@ukl:dnum]/text()", namespaces=namespaces)
        logger.debug(f"Amendment Order from Checking File: {amendment_order}")

        # Order amendment groups based on checking file order
        for amendment_number in amendment_order:
            if amendment_number in remaining_amendments:
                logger.debug(f"Found matching amendment: {amendment_number}")
                ordered_amendment_groups.append((amendment_number, remaining_amendments.pop(amendment_number)))
                was_reordered = True  # Mark as reordered
            else:
                logger.debug(f"Amendment '{amendment_number}' not found in amendment groups.")

    # Always process remaining amendments
    if remaining_amendments:
        logger.debug(f"Adding unmatched amendments for bill '{bill_title}': {list(remaining_amendments.keys())}")
    for unmatched_amendment in remaining_amendments.keys():
        ordered_amendment_groups.append((unmatched_amendment, remaining_amendments[unmatched_amendment]))

    return ordered_amendment_groups, was_reordered

def generate_html(xml_file, checking_file_paths, eligible_members):
    """
    Generates HTML content, splitting it into summary and bill sections.

    Args:
        xml_file (str): Path to the input XML file.
        checking_file_paths (list): Paths to parsed marshalling XML files.
        eligible_members (set): Set of eligible members from the API.

    Returns:
        tuple: The summary section and the bill section as HTML strings.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Load checking files
    checking_files = get_marshal_xml(checking_file_paths)

    # Initialize the root element for dynamic content
    html = ET.Element("div", {"class": "dynamic-content"})

    # Summary Section
    main_summary_div = ET.Element("div", {"class": "main-summary"})
    report_date = root.findtext(".//downloaded")
    if report_date:
        ET.SubElement(main_summary_div, "h1").text = f"{report_date}"
    paper_count = len(set(item.find("bill").text for item in root.findall(".//item")))
    if paper_count > 1:
        ET.SubElement(main_summary_div, "p").text = f"{paper_count} papers have added names today:"
    else:
        ET.SubElement(main_summary_div, "p").text = "Only one paper has added names today:"

    # List of bills
    bill_list = ET.SubElement(main_summary_div, "ul")
    bills = set(item.find("bill").text for item in root.findall(".//item"))
    for bill in sorted(bills):
        li = ET.SubElement(bill_list, "li")
        ET.SubElement(
            li,
            "a",
            {"href": f"#{bill.lower().replace(' ', '-')}", "style": "color:white"},
        ).text = bill

    # Explanatory text
    if checking_files:
        explanatory_text_1 = ET.SubElement(main_summary_div, "p")
        explanatory_text_1.text = "If you provide LawMaker XML: "
        ET.SubElement(explanatory_text_1, "span", {"class": "green"}).text = " ✔"
        ET.SubElement(explanatory_text_1, "span").text = (
            " indicates that names have been added already, "
        )
        ET.SubElement(explanatory_text_1, "span", {"class": "red"}).text = " ✘"
        ET.SubElement(explanatory_text_1, "span").text = (
            " indicates that the name has not yet been added (at least not in the XML provided). "
            "You can turn these indicators on or off: "
        )
        ET.SubElement(
            explanatory_text_1, "button", {"id": "name-in-xml-indicator-toggle-btn"}
        ).text = "Turn off"

        explanatory_text_2 = ET.SubElement(main_summary_div, "p")
        explanatory_text_2.text = "The following XML files have been used for marshalling: "
        ET.SubElement(
            explanatory_text_2, "button", {"id": "show-hide-marshalling-xml-files-btn"}
        ).text = "Show files"

        # Collapsible XML files list
        collapsible_div = ET.SubElement(
            main_summary_div, "div", {"id": "collapsible-xml-files", "style": "display: none;"}
        )
        ul = ET.SubElement(collapsible_div, "ul")
        for checking_file in checking_files:
            li = ET.SubElement(ul, "li")
            li.text = (
                os.path.basename(checking_file.getroot().base)
                if checking_file.getroot().base
                else "Unknown file"
            )
    else:
        explanatory_text = ET.SubElement(main_summary_div, "p")
        explanatory_text.text = "No marshalling XML found."

    summary_section = ET.tostring(
        main_summary_div, pretty_print=True, method="html", encoding="unicode"
    )

    # Make a div for each bill
    for bill in sorted(bills):
        bill_div = ET.SubElement(
            html, "div", {"class": "bill", "id": bill.lower().replace(" ", "-")}
        )
        ET.SubElement(bill_div, "h1", {"class": "bill-title"}).text = bill

        # Initialize amendment_groups as a dictionary
        amendment_groups = {}
        for item in root.findall(".//item"):
            if item.findtext("bill") == bill:
                for amd_no in item.findall(".//matched-numbers/amd-no"):
                    amd_number = amd_no.text
                    if amd_number not in amendment_groups:
                        amendment_groups[amd_number] = {"items": [], "comments": []}
                    # Add the item and comments
                    amendment_groups[amd_number]["items"].append(item)
                    comments = item.find(".//comments")
                    if comments is not None:
                        amendment_groups[amd_number]["comments"].extend(
                            comments.findall("p")
                        )

        # Provide a count of amendment groups in each bill;
        number_summary_count_div = ET.SubElement(bill_div, "div", {"class": "number-summary-count"})
        p = ET.SubElement(number_summary_count_div, "p")
        p.text = "Amendments in this paper with names added/removed: "
        ET.SubElement(p, "b").text = str(len(amendment_groups))

        # Check for checking files and reorder amendments if available
        if checking_files:
            ordered_amendments, was_reordered = reorder_amendments(
                checking_files, bill, amendment_groups
            )
        else:
            # Fall back to unordered amendments
            logger.info(f"No valid checking files found for bill '{bill}'. Rendering amendments in original order.")
            ordered_amendments = list(amendment_groups.items())
            was_reordered = False

        # Render amendments (ordered or unordered based on availability of checking files)
        if not amendment_groups:
            logger.debug(f"No amendments found for bill '{bill}'.")
        else:
            for amd_number, group in ordered_amendments:
                amendment_div = ET.SubElement(bill_div, "div", {"class": "amendment"})
                ET.SubElement(amendment_div, "div", {"class": "bill-reminder"}).text = bill
                num_info = ET.SubElement(amendment_div, "div", {"class": "num-info"})
                h2 = ET.SubElement(num_info, "h2", {"class": "amendment-number"})

                # Add fallback warning if amendments are not reordered
                if not checking_files or not was_reordered:
                    h2.text = f"{amd_number}"
                    warning_span = ET.SubElement(
                        h2,
                        "span",
                        {
                            "style": "font-family:Segoe UI Symbol;color:red;font-weight:normal;padding-left:10px",
                            "title": "This amendment is not shown in marshalled order. It may be that the amendment has been withdrawn, it is newly tabled, or no XML was supplied to determine marshalled order.",
                        },
                    )
                    warning_span.text = "⚠"
                else:
                    h2.text = f"{amd_number}"

                # Add prefix for non-NC/NS amendments
                if not re.match(r"(NC|NS)", amd_number):
                    h2.text = f"Amendment {amd_number}"
                else:
                    h2.text = amd_number

                # Render names to add
                names_to_add_div = ET.SubElement(amendment_div, "div", {"class": "names-to-add"})
                ET.SubElement(names_to_add_div, "h4").text = "Names to add"

                for item in group["items"]:

                    matched_names = item.find(".//names-to-add/matched-names")
                    if not iselement(matched_names):
                        continue

                    for name in matched_names.findall("name"):
                        name_text = name.text
                        name_div = ET.SubElement(names_to_add_div, "div", {"class": "name"})
                        name_span = ET.SubElement(name_div, "span")

                        # Style based on whether the name matches MNIS
                        style = (
                            "text-decoration: none; color: black;"
                            if name_text in eligible_members
                            else "text-decoration: underline red 1px; color: black;"
                        )
                        ET.SubElement(
                            name_span,
                            "a",
                            {
                                "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                                "href": f"https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID={item.find('dashboard-id').text}",
                                "style": style,
                            },
                        ).text = name_text

                # Render names to remove

                if any(item.find(".//names-to-remove/matched-names") is not None for item in group["items"]):
                    names_to_remove_div = ET.SubElement(amendment_div, "div", {"class": "names-to-remove"})
                    ET.SubElement(names_to_remove_div, "h4").text = "Names to remove"
                    for item in group["items"]:

                        matched_names = item.find(".//names-to-remove/matched-names")
                        if not iselement(matched_names):
                            continue

                        for name in matched_names.findall("name"):
                            name_text = name.text
                            name_div = ET.SubElement(names_to_remove_div, "div", {"class": "name"})
                            name_span = ET.SubElement(name_div, "span")

                            ET.SubElement(
                                name_span,
                                "a",
                                {
                                    "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                                    "href": f"https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID={item.find('dashboard-id').text}",
                                    "style": style,
                                },
                            ).text = name_text

                # Comments Section
                if group["comments"]:
                    comments_div = ET.SubElement(amendment_div, "div", {"class": "comments"})
                    ET.SubElement(comments_div, "h4", {"style": "margin-bottom:5px;margin-top:30px;"}).text = "Comments"

                    for comment in group["comments"]:
                        parent_comments = comment.getparent()
                        dashboard_id = parent_comments.get("dashboard-id") if iselement(parent_comments) else None
                        comment_url = f"https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID={dashboard_id}" if dashboard_id else None

                        if dashboard_id:
                            dashboard_link_p = ET.SubElement(
                                comments_div, "p", {"style": "font-size:smaller;color:#4d4d4d;"}
                            )

                            dashboard_link_a = ET.SubElement(
                                dashboard_link_p,
                                "a",
                                {"href": comment_url, "style": "text-decoration:none;color:#4d4d4d;"},
                            )
                            ET.SubElement(dashboard_link_a, "b").text = f"Dashboard ID: {dashboard_id}"

                        comment_p = ET.SubElement(
                            comments_div,
                            "p",
                            {"title": f"Dashboard ID:{dashboard_id}" if dashboard_id else "No Dashboard ID"},
                        )
                        if comment.text:
                            comment_text_p = ET.SubElement(
                                comments_div,
                                "p",
                                {
                                    "title": f"Dashboard ID:{dashboard_id}" if dashboard_id else "",
                                    "style": "font-size:smaller;color:#4d4d4d;line-height:90%;",
                                },
                            )
                            ET.SubElement(comment_text_p, "i").text = comment.text.strip()

                    # Add checkbox for each comment
                    checkbox_div = ET.SubElement(comments_div, "div", {"class": "check-box"})
                    checkbox_input = ET.SubElement(checkbox_div, "input", {"type": "checkbox"})
                    checkbox_label = ET.SubElement(checkbox_div, "label")
                    checkbox_label.text = "Checked"

    bill_section = ET.tostring(
        html, pretty_print=True, method="html", encoding="unicode"
    )

    return summary_section, bill_section

def inject_html_template(template_path, output_path, summary_content, dynamic_content):
    """
    Injects content into the HTML template.
    """
    # Read the HTML template
    with open(template_path, "r", encoding="utf-8") as template_file:
        template_html = template_file.read()

    # Replace placeholders with our stuff
    template_html = template_html.replace("{{summary}}", summary_content)
    template_html = template_html.replace("{{content}}", dynamic_content)

    # Write the result to the output file
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(template_html)

    print(f"HTML file successfully generated: {output_path}")

# Add ticks and crosses to the HTML file according to the marshalling XML
def ticks_and_crosses(output_html_file_path, marshal_file_dir):
    """
    Annotates HTML file with indicators (✔/✘) based on matches in marshal XML.
    """
    # Load the existing HTML file
    try:
        parser = ET.HTMLParser()
        with open(output_html_file_path, 'r', encoding='utf-8') as html_file:
            html_tree = ET.parse(html_file, parser)
    except Exception as e:
        logger.error(f"Failed to load HTML file: {e}")
        return

    # Collect marshal XML files
    checking_files = []
    if os.path.isdir(marshal_file_dir):  # TODO: change to Path
        for file_name in os.listdir(marshal_file_dir):
            if file_name.endswith('.xml'):
                try:
                    checking_files.append((file_name, ET.parse(os.path.join(marshal_file_dir, file_name))))
                except Exception as e:
                    logger.warning(f"Failed to parse checking file '{file_name}': {e}")

    if not checking_files:
        logger.info("No valid checking files found. Skipping annotations.")
        return

    # Annotate the HTML file
    for bill_div in html_tree.xpath("//div[@class='bill']"):
        bill_title = bill_div.find(".//h1[@class='bill-title']")
        if bill_title is None or not bill_title.text:
            continue
        bill_name = bill_title.text.strip()

        for amendment_div in bill_div.xpath(".//div[@class='amendment']"):
            amendment_number_element = amendment_div.find(".//div[@class='num-info']/h2[@class='amendment-number']")
            if amendment_number_element is None or not amendment_number_element.text:
                continue
            amendment_number = amendment_number_element.text.strip().replace("Amendment ", "")  # Remove "Amendment "

            for name_div in amendment_div.xpath(".//div[@class='names-to-add']/div[@class='name']"):
                name_anchor = name_div.find(".//a")
                if name_anchor is None or not name_anchor.text:
                    logger.debug(f"Skipping name without anchor text in amendment {amendment_number}.")
                    continue
                name_text = name_anchor.text.strip()
                annotation = "✘"

                logger.debug(f"Checking name: {name_text} for amendment {amendment_number} in bill {bill_name}")

                for file_name, checking_file in checking_files:
                    logger.debug(f"Processing checking file: {file_name}")
                    try:
                        root = checking_file.getroot()

                        # Check if bill name matches
                        bill_matches = root.xpath(
                            f'/akomaNtoso/amendmentList/meta/references/TLCConcept[@showAs="{bill_name}"]',
                            namespaces={"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
                        )
                        if not bill_matches:
                            logger.debug(f"No match for bill: {bill_name} in file: {file_name}.")
                            continue

                        # Match the amendment by number using <num> element with @ukl:dnum
                        amendment_numbers = [
                            elem.text.strip() for elem in root.xpath(
                                "/akomaNtoso/amendmentList/component/amendment/amendmentBody/akn:num[@ukl:dnum]",
                                namespaces={"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
                                            "ukl": "https://www.legislation.gov.uk/namespaces/UK-AKN"}
                            )
                        ]
                        if amendment_number not in amendment_numbers:
                            logger.debug(f"Amendment number {amendment_number} not found in file: {file_name}.")
                            continue

                        # Match the name in proposer/supporter blocks
                        proposer_supporter_blocks = root.xpath(
                            f"/akomaNtoso/amendmentList/component/amendment[amendmentBody/akn:num[text()='{amendment_number}']]"
                            "/amendmentHeading/block[@name='proposer' or @name='supporters']",
                            namespaces={"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
                        )
                        for block in proposer_supporter_blocks:
                            if any(name_text == elem.text.strip() for elem in block.xpath(".//docIntroducer | .//docProponent")):
                                annotation = "✔"
                                break
                    except Exception as e:
                        logger.error(f"Error processing checking file: {file_name}, error: {e}")

                # Add annotation span
                annotation_span = ET.SubElement(
                    name_div, "span",
                    {"class": f"green name-in-xml-indicator" if annotation == "✔" else "red name-in-xml-indicator",
                     "title": "This name appears to have been added." if annotation == "✔" else "This name does not appear to have been added."}
                )
                annotation_span.text = f" {annotation}"

    # Save the updated HTML
    try:
        with open(output_html_file_path, 'wb') as output_file:
            output_file.write(ET.tostring(html_tree, pretty_print=True, method='html', encoding='utf-8'))
    except Exception as e:
        logger.error(f"Failed to save annotated HTML: {e}")


def main(template_path, xml_file_path, marshal_file_dir, output_html_file_path):
    """Main function to execute the transformation."""
    try:
        # Fetch eligible members from MNIS API
        eligible_members = fetch_eligible_members()

        # Generate HTML content
        summary_content, bill_content = generate_html(xml_file_path, marshal_file_dir, eligible_members)

        # Inject content into the HTML template
        inject_html_template(template_path, output_html_file_path, summary_content, bill_content)

        # Annotate ticks and crosses
        ticks_and_crosses(output_html_file_path, marshal_file_dir)

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python anr_post_processing_html.py <template_path> <xml_file_path> <marshal_file_dir> <output_html_file_path>")
        sys.exit(1)

    template_path = sys.argv[1]
    xml_file_path = sys.argv[2]
    marshal_file_dir = sys.argv[3]
    output_html_file_path = sys.argv[4]
    main(template_path, xml_file_path, marshal_file_dir, output_html_file_path)
