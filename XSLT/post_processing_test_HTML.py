import os
from lxml import etree as ET

# ? Testing with local XML file
xml_file_path = 'output.xml'
output_html_file_path = 'output.html'

# MNIS data for name checks
mnis_name_url = 'http://data.parliament.uk/membersdataplatform/services/mnis/members/query/House=Commons%7CIsEligible=true/'
mnis_name_tree = ET.parse(mnis_name_url)
mnis_name_root = mnis_name_tree.getroot()

def generate_html(xml_file, output_html_file, marsh_path=None):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # HTML begin
    html = ET.Element("html")
    head = ET.SubElement(html, "head")
    ET.SubElement(head, "title").text = "Added Names Report"

    # CSS styles
    style = ET.SubElement(head, "style")
    style.text = (
        "html {font-family:'Segoe UI', Frutiger, 'Frutiger Linotype', 'Dejavu Sans', 'Helvetica Neue', Arial, sans-serif;background-color:#ebe9e8;;word-wrap:normal;white-space:normal;}"
        "body {width:70%;background-color:#ffffff;margin-left:30px;margin:auto;overflow-wrap: break-word;padding-bottom:20px;}"
        ".header {background-color:#373151;color:#ffffff;}"
        ".number-summary-count {padding-left:20px;margin-bottom:20px}"
        ".amendment {margin-bottom:20px;margin-left:20px;border:2px solid #ebe9e8;padding-left:10px;width:30%;min-width:200px;padding-bottom:10px}"
        ".bill-title {color:black;padding-left:20px;} hr {color:#006e46;}"
        ".bill-reminder {text-align:right;color:#4d4d4d;font-size:10px;padding-right:5px;}"
        ".num-info {border-bottom: 1px dotted #ebe9e8;}"
        ".main-heading {padding-left:20px;padding-top:20px;}"
        ".main-summary {padding:0 0 10px 20px}"
        ".red {color:red} .green {color:green}")

    body = ET.SubElement(html, "body")

    # Header section
    header_div = ET.SubElement(body, "div", {"class": "header"})
    main_heading_div = ET.SubElement(header_div, "div", {"class": "main-heading"})
    main_heading = ET.SubElement(main_heading_div, "h1")
    main_heading.text = "Added Names report"
    line_break = ET.SubElement(main_heading, "br")
    downloaded_value = root.find(".//downloaded") # Get the date of the report
    if downloaded_value is not None:
        line_break.tail = downloaded_value.text

    main_summary_div = ET.SubElement(header_div, "div", {"class": "main-summary"})
    item_count = len(set(item.find("bill").text for item in root.findall('.//item')))
    if item_count > 1:
        paper_count_text = f"{item_count} papers have added names today:"
    else:
        paper_count_text = f"Only one paper has added names today:"
    ET.SubElement(main_summary_div, "p").text = paper_count_text

    # List of bills
    bill_list = ET.SubElement(main_summary_div, "ul")
    bills = set(item.find("bill").text for item in root.findall(".//item"))
    for bill in sorted(bills):
        li = ET.SubElement(bill_list, "li")
        ET.SubElement(li, "a", {"href": f"#{bill.lower().replace(' ', '-')}", "style": "color:white"}).text = bill

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

            # Add "Amendment" prefix to amendment numbers
            if not (amd_number.startswith("NC") or amd_number.startswith("NS")):
                ET.SubElement(num_info, "h2", {"class": "amendment-number"}).text = f"Amendment {amd_number}"
            else:
                ET.SubElement(num_info, "h2", {"class": "amendment-number"}).text = amd_number

            # Names to add
            names_to_add_div = ET.SubElement(amendment_div, "div", {"class": "names-to-add"})
            ET.SubElement(names_to_add_div, "h4").text = "Names to add"
            for item in group["items"]:
                matched_names = item.find(".//names-to-add/matched-names")
                if matched_names is not None:
                    for name in matched_names.findall("name"):
                        name_div = ET.SubElement(names_to_add_div, "div", {"class": "name"})
                        name_span = ET.SubElement(name_div, "span")
                        ET.SubElement(name_span, "a", {
                            "title": f"Dashboard ID:{item.find('dashboard-id').text}",
                            "href": f"https://hopuk.sharepoint.com/sites/bct-ppu/Lists/AddNames/DispForm.aspx?ID={item.find('dashboard-id').text}",
                            "style": "text-decoration: none; color:black"
                        }).text = name.text

            # Comments
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
