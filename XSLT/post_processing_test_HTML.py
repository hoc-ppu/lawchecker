import os
import requests
from lxml import etree as ET

# ? Testing with local XML files for now
xml_file_path = 'output.xml'
output_html_file_path = 'output.html'
marshalling_file_paths = ['..\\example_files\\addedNames\\Amendment_Paper_XML\\victims_prisoners_rm_pbc_0628.xml']

def load_marshalling_xml(paths):
    """Load additional XML files for checking amendments."""
    checking_files = []
    for path in paths:
        try:
            tree = ET.parse(path)
            checking_files.append(tree)
            print(f"Loaded checking XML file: {path}")  # Debug: Output file path for verification
        except ET.XMLSyntaxError as e:
            print(f"Error parsing {path}: {e}")
    return checking_files

def fetch_eligible_members():
    """Fetches list of current members from MNIS for name checking."""
    url = "https://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons|IsEligible=true/"
    response = requests.get(url)
    if response.status_code == 200:
        members_tree = ET.fromstring(response.content)
        # Extract <DisplayAs> text for each <Member> in the API response
        return {member.find("DisplayAs").text for member in members_tree.findall(".//Member") if member.find("DisplayAs") is not None}
    else:
        print("Failed to fetch data from MNIS API.")
        return set()

def generate_html(xml_file, output_html_file, checking_files, eligible_members):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Function to check amendments in additional XML files
    def check_amendment_in_files(amendment_num, bill_key):
        """Check if amendment exists in any loaded checking XML files based on certain criteria."""
        for file_tree in checking_files:
            # Extract namespaces from the XML file
            namespaces = {k if k else 'default': v for k, v in file_tree.getroot().nsmap.items()}
        
            # Use namespace-aware XPath query
            try:
                xpath_query = (
                    f"//*[normalize-space(ancestor::*[local-name()='TLCConcept' and @eId='varBillTitle']/@showAs) = '{bill_key}' "
                    f"and descendant::*[local-name()='num' and @ukl:dnum = '{amendment_num}']] | "
                    f"//Amendments.Commons[normalize-space(replace(descendant::*[local-name()='STText'], ', As Amended', '')) = '{bill_key}']"
                )
                matches = file_tree.xpath(xpath_query, namespaces=namespaces)
                
                if matches:
                    print(f"[DEBUG] Found matches for amendment '{amendment_num}' under bill '{bill_key}':")
                    for match in matches:
                        print(f" - Match: {ET.tostring(match, pretty_print=True).decode('utf-8')}")
                    return True
                else:
                    print(f"[DEBUG] No matches found for amendment '{amendment_num}' under bill '{bill_key}'.")
                    return False
            except ET.XPathEvalError as e:
                print(f"[ERROR] XPath evaluation error: {e}")
                return False


    # Create the HTML structure
    html = ET.Element("html")
    head = ET.SubElement(html, "head")
    ET.SubElement(head, "meta", {"http-equiv": "Content-Type", "content": "text/html; charset=UTF-8"})
    ET.SubElement(head, "title").text = "Added Names Report"
    
    style = ET.SubElement(head, "style")
    style.text = (
        "html {font-family:'Segoe UI', Frutiger, 'Frutiger Linotype', 'Dejavu Sans', "
        "'Helvetica Neue', Arial, sans-serif; background-color:#ebe9e8; word-wrap:normal; "
        "white-space:normal;} body {width:70%; background-color:#ffffff; margin:auto; "
        "overflow-wrap: break-word; padding-bottom:20px;} .header {background-color:#373151; "
        "color:#ffffff;} .number-summary-count {margin-bottom:20px;} .amendment {margin-bottom:20px; "
        "margin-left:20px; border:2px solid #ebe9e8; padding-left:10px; width:80%; min-width:200px; "
        "padding-bottom:10px;} .bill-title {color:black; background-color:#ffffff; padding-left:20px;} "
        "hr {color:#006e46;} .main-heading {padding-left:20px; padding-top:20px;} .main-summary {padding:0 0 10px 20px;} "
        ".num-info {border-bottom:1px dotted #ebe9e8;} .bill-reminder {text-align:right; color:#4d4d4d; font-size:10px; padding-right:5px;}"
    )

    body = ET.SubElement(html, "body")

    # Header section
    header_div = ET.SubElement(body, "div", {"class": "header"})
    main_heading_div = ET.SubElement(header_div, "div", {"class": "main-heading"})
    main_heading = ET.SubElement(main_heading_div, "h1")
    main_heading.text = "Added Names report"
    ET.SubElement(main_heading, "br")
    downloaded_value = root.find(".//downloaded")
    if downloaded_value is not None:
        main_heading.tail = downloaded_value.text

    # Main summary section
    main_summary_div = ET.SubElement(header_div, "div", {"class": "main-summary"})
    paper_count = len(root.findall(".//item"))
    if paper_count > 1:
        ET.SubElement(main_summary_div, "p").text = f"{paper_count} papers have added names today:"
    else:
        ET.SubElement(main_summary_div, "p").text = "Only one paper has added names today:"
    
    # List of bills
    bill_list = ET.SubElement(main_summary_div, "ul")
    bills = set(item.find("bill").text for item in root.findall(".//item"))
    for bill in sorted(bills):
        li = ET.SubElement(bill_list, "li")
        ET.SubElement(li, "a", {"href": f"#{bill.lower().replace(' ', '-')}", "style": "color:white"}).text = bill

      # Add the LawMaker XML instructions
    p1 = ET.SubElement(main_summary_div, "p")
    p1.text = "If you provide LawMaker XML: "
    span_green = ET.SubElement(p1, "span", {"class": "green"})
    span_green.text = " ✔"
    p1_tail = ET.SubElement(p1, "span")
    p1_tail.text = " indicates that names have been added already, "
    
    span_red = ET.SubElement(p1, "span", {"class": "red"})
    span_red.text = " ✘"
    p1_tail2 = ET.SubElement(p1, "span")
    p1_tail2.text = (
        " indicates that the name has not yet been added (at least not in the XML provided). "
        "You can turn these indicators on or off: "
    )
    button_toggle = ET.SubElement(p1_tail2, "button", {"id": "name-in-xml-indicator-toggle-btn"})
    button_toggle.text = "Turn off"

    p2 = ET.SubElement(main_summary_div, "p")
    p2.text = "The following XML files have been used for marshalling: "
    button_show_files = ET.SubElement(p2, "button", {"id": "show-hide-marshalling-xml-files-btn"})
    button_show_files.text = "Show files"

    # Collapsible div for XML files
    collapsible_div = ET.SubElement(main_summary_div, "div", {"id": "collapsible-xml-files", "style": "display: none;"})
    ul = ET.SubElement(collapsible_div, "ul")

    # Iterate over XML files and add to the list
    for path in marshalling_file_paths:
        li = ET.SubElement(ul, "li")
        li.text = os.path.basename(path)

    # Generate content for each bill
    for bill in sorted(bills):
        bill_div = ET.SubElement(body, "div", {"class": "bill", "id": bill.lower().replace(' ', '-')})
        ET.SubElement(bill_div, "h1", {"class": "bill-title"}).text = bill

        bill_items = [item for item in root.findall(".//item") if item.find("bill").text == bill]
        amendment_groups = {}
        for item in bill_items:
            for amd_no in item.findall(".//matched-numbers/amd-no"):
                amd_number = amd_no.text
                if amd_number not in amendment_groups:
                    amendment_groups[amd_number] = {"items": [], "comments": []}
                amendment_groups[amd_number]["items"].append(item)
                comments = item.find(".//comments")
                if comments is not None:
                    amendment_groups[amd_number]["comments"].extend(comments.findall("p"))

        for amd_number, group in amendment_groups.items():
            amendment_div = ET.SubElement(bill_div, "div", {"class": "amendment"})
            ET.SubElement(amendment_div, "div", {"class": "bill-reminder"}).text = bill
            num_info = ET.SubElement(amendment_div, "div", {"class": "num-info"})
            
            # Check the amendment in external files and add prefix if not found
            if check_amendment_in_files(amd_number, bill):
                amendment_text = amd_number
            else:
                amendment_text = f"Amendment {amd_number}"
            
            amendment_heading = ET.SubElement(num_info, "h2", {"class": "amendment-number"})
            amendment_heading.text = amendment_text
            
            # Add a warning for missing amendments
            if not check_amendment_in_files(amd_number, bill):
                warning_span = ET.SubElement(amendment_heading, "span", {
                    "style": "font-family:Segoe UI Symbol;color:red;font-weight:normal;padding-left:10px",
                    "title": "This amendment is not shown in marshalled order. It may be that the amendment has been withdrawn, it is newly tabled, or no XML was supplied to determine marshalled order."
                })
                warning_span.text = "⚠"

            # Names to Add Section
            names_to_add_div = ET.SubElement(amendment_div, "div", {"class": "names-to-add"})
            ET.SubElement(names_to_add_div, "h4").text = "Names to add"
            for item in group["items"]:
                matched_names = item.find(".//names-to-add/matched-names")
                if matched_names is not None:
                    for name in matched_names.findall("name"):
                        name_text = name.text
                        name_div = ET.SubElement(names_to_add_div, "div", {"class": "name"})
                        name_span = ET.SubElement(name_div, "span")
                        
                        # Apply style based on whether the name matches eligible members
                        if name_text in eligible_members:
                            style = "text-decoration: none; color: black;"
                        else:
                            style = "text-decoration: underline red 1px; color: black;"

                        ET.SubElement(name_span, "a", {
                            "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                            "href": f"https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID={item.find('dashboard-id').text}",
                            "style": style
                        }).text = name_text

            # Comments Section
            if group["comments"]:
                comments_div = ET.SubElement(amendment_div, "div", {"class": "comments"})
                ET.SubElement(comments_div, "h5", {"style": "margin-bottom:5px"}).text = "Comments on dashboard"
                for comment in group["comments"]:
                    p = ET.SubElement(comments_div, "p", {
                        "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                        "style": "font-size:smaller; color:#4d4d4d;"
                    })
                    p.text = comment.text

    html_tree = ET.ElementTree(html)
    html_tree.write(output_html_file, pretty_print=True, method="html", encoding="UTF-8")
    print(f"HTML generation completed. Output saved to {output_html_file}")

marshalling_files = load_marshalling_xml(marshalling_file_paths)
eligible_members = fetch_eligible_members()
generate_html(xml_file_path, output_html_file_path, marshalling_files, eligible_members)
