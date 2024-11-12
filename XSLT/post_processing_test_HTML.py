import os
import requests
from lxml import etree as ET

# ? Testing with local XML file
xml_file_path = 'output.xml'
output_html_file_path = 'output.html'


def generate_html(xml_file, output_html_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Fetch and parse eligible member names from the API
    def fetch_eligible_members():
        url = "https://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons|IsEligible=true/"
        response = requests.get(url)
        if response.status_code == 200:
            members_tree = ET.fromstring(response.content)
            # Extract <DisplayAs> text for each <Member> in the API response
            return {member.find("DisplayAs").text for member in members_tree.findall(".//Member") if member.find("DisplayAs") is not None}
        else:
            print("Failed to fetch data from MNIS API.")
            return set()

    # Retrieve eligible members for matching
    eligible_members = fetch_eligible_members()  # Ensure we call the function

    # Create the HTML structure
    html = ET.Element("html")
    head = ET.SubElement(html, "head")
    
    # Meta and Title
    ET.SubElement(head, "meta", {"http-equiv": "Content-Type", "content": "text/html; charset=UTF-8"})
    ET.SubElement(head, "title").text = "Added Names Report"
    
    # Add CSS styles
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
    
    # Create the <h1> with line break and .//downloaded value
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
    for file in root.findall(".//item"):  # Adjust this XPath as necessary to point to your XML file paths
        li = ET.SubElement(ul, "li")
        li.text = file.find("file-name").text if file.find("file-name") is not None else "Unknown file"

    # Generate content for each bill
    for bill in sorted(bills):
        bill_div = ET.SubElement(body, "div", {"class": "bill", "id": bill.lower().replace(' ', '-')})
        ET.SubElement(bill_div, "h1", {"class": "bill-title"}).text = bill

        # Find all items for this bill
        bill_items = [item for item in root.findall(".//item") if item.find("bill").text == bill]

        # Group names and comments by amendment number
        amendment_groups = {}
        for item in bill_items:
            for amd_no in item.findall(".//matched-numbers/amd-no"):
                amd_number = amd_no.text
                if amd_number not in amendment_groups:
                    amendment_groups[amd_number] = {"items": [], "comments": []}
                amendment_groups[amd_number]["items"].append(item)
                # Collect associated comments for this amendment
                comments = item.find(".//comments")
                if comments is not None:
                    amendment_groups[amd_number]["comments"].extend(comments.findall("p"))

        # Generate HTML for each amendment group
        for amd_number, group in amendment_groups.items():
            amendment_div = ET.SubElement(bill_div, "div", {"class": "amendment"})
            ET.SubElement(amendment_div, "div", {"class": "bill-reminder"}).text = bill
            num_info = ET.SubElement(amendment_div, "div", {"class": "num-info"})
            ET.SubElement(num_info, "h2", {"class": "amendment-number"}).text = amd_number

            # Names to add
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

            # Comments section
            if group["comments"]:
                comments_div = ET.SubElement(amendment_div, "div", {"class": "comments"})
                ET.SubElement(comments_div, "h5", {"style": "margin-bottom:5px"}).text = "Comments on dashboard"
                for comment in group["comments"]:
                    p = ET.SubElement(comments_div, "p", {
                        "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                        "style": "font-size:smaller; color:#4d4d4d;"
                    })
                    p.text = comment.text


    
    # Generate HTML file
    html_tree = ET.ElementTree(html)
    html_tree.write(output_html_file, pretty_print=True, method="html", encoding="UTF-8")
    print(f"HTML generation completed. Output saved to {output_html_file}")

generate_html(xml_file_path, output_html_file_path)
