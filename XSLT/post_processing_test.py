import re
from lxml import etree
from datetime import datetime

# A - tidy XML

# ? Testing with local XML file
xml_file = '..\\XML\\2021-12-02_added-names.xml'  # Replace with your input XML file path
xml_tree = etree.parse(xml_file)

# Create a new root element for the output
root = etree.Element("root")

# Define namespaces
namespaces = {
    'm': 'http://schemas.microsoft.com/ado/2007/08/dataservices/metadata',
    'd': 'http://schemas.microsoft.com/ado/2007/08/dataservices',
    'atom': 'http://www.w3.org/2005/Atom'  # Default namespace for 'feed' elements
}

# Apply element templates
def apply_templates(element, parent):
    for child in element:
        new_element = etree.SubElement(parent, child.tag)
        if child.text:
            new_element.text = child.text
        apply_templates(child, new_element)

# Get required fields from 'm:properties' element
def m_properties(element, parent, namespaces):
    # Create 'item' element
    item = etree.SubElement(parent, "item")

    # We want the following child elements
    for child in element:
        if child.tag == f"{{{namespaces['d']}}}Id":
            id_element = etree.SubElement(item, "dashboard-id")
            id_element.text = child.text
        elif child.tag == f"{{{namespaces['d']}}}Bill":
            bill_element = etree.SubElement(item, "bill")
            bill_element.text = child.text
        elif child.tag == f"{{{namespaces['d']}}}Amendments":
            numbers_element = etree.SubElement(item, "numbers")
            original_string = etree.SubElement(numbers_element, "original-string")
            original_string.text = child.text.strip() if child.text else ""
            matched_numbers = etree.SubElement(numbers_element, "matched-numbers")
            amd_no = etree.SubElement(matched_numbers, "amd-no")
            amd_no.text = child.text.strip() if child.text else ""
        elif child.tag == f"{{{namespaces['d']}}}Names":
            names(child, item, namespaces)
        elif child.tag == f"{{{namespaces['d']}}}Namestoremove":
            names_to_remove(child, item, namespaces)
        elif child.tag == f"{{{namespaces['d']}}}PPU_x002d_omitfromreport":
            omit_from_report(child, item)
        elif child.tag == f"{{{namespaces['d']}}}Comments":
            comments(child, item, namespaces)

# 'd:Bill' element
def bill(element, parent):
    bill = etree.SubElement(parent, "bill")
    bill.text = element.text

# 'd:Id' element
def id(element, parent):
    dashboard_id = etree.SubElement(parent, "dashboard-id")
    dashboard_id.text = element.text

# 'd:Amendments' element incl. regex patterns
def amendments(element, parent):
    numbers = etree.SubElement(parent, "numbers")

    # Normalize
    original_text = element.text.strip() if element.text else ""
    original_string = etree.SubElement(numbers, "original-string")
    original_string.text = original_text

    # Create 'matched-numbers' element
    matched_numbers = etree.SubElement(numbers, "matched-numbers")

    # Tokenize
    tokens = re.split(r'\n|,|;| and | &amp; |\+', original_text)

    # Regex patterns
    range_pattern = re.compile(r'(\d+)\s?[-–—]\s?(\d+)') # Hyphen-like characters
    amendment_pattern = re.compile(r'(A|Amendment|amendment|Amendments|Amdt|amdt|A):?\s?(\d{1,3})') # Amendment-like prefixes
    nc_pattern = re.compile(r'(NC|New Clause|new clause)\s?(\d{1,3})') # New Clause-like prefixes
    ns_pattern = re.compile(r'(NS|New Schedule|new schedule)\s?(\d{1,3})') # New Schedule-like prefixes
    single_number_pattern = re.compile(r'\d{1,3}') # Single numbers

    # Process tokens
    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Check for ranges with hyphen-like characters
        if range_pattern.match(token):
            start, end = map(int, range_pattern.match(token).groups())
            for num in range(start, end + 1):
                amd_no = etree.SubElement(matched_numbers, "amd-no")
                amd_no.text = str(num)
                                  
        # Check for amendments prefixed by "Amendment", "Amdt", etc.
        elif amendment_pattern.match(token):
            number = amendment_pattern.match(token).group(2)
            amd_no = etree.SubElement(matched_numbers, "amd-no")
            amd_no.text = number

        # Check for "NC" or "New Clause"
        elif nc_pattern.match(token):
            number = nc_pattern.match(token).group(2)
            amd_no = etree.SubElement(matched_numbers, "amd-no")
            amd_no.text = f"NC{number}"

        # Check for "NS" or "New Schedule"
        elif ns_pattern.match(token):
            number = ns_pattern.match(token).group(2)
            amd_no = etree.SubElement(matched_numbers, "amd-no")
            amd_no.text = f"NS{number}"

        # Check for single numbers
        elif single_number_pattern.match(token):
            number = single_number_pattern.match(token).group(0)
            amd_no = etree.SubElement(matched_numbers, "amd-no")
            amd_no.text = number
        else:
            # If the token does not match any pattern, add to 'unmatched-numbers-etc'
            unmatched_numbers = etree.SubElement(numbers, "unmatched-numbers-etc")
            unmatched_numbers.text = token

def names(element, parent, namespaces):
    # Create the container element for 'names-to-add'
    container_element = etree.SubElement(parent, "names-to-add")
    
    # Extract and normalize the original text
    original_text = element.text.strip() if element.text else ""
    original_string = etree.SubElement(container_element, "original-string")
    original_string.text = original_text

    # Create 'matched-names' element
    matched_names = etree.SubElement(container_element, "matched-names")
    
    # Tokenize
    tokens = re.split(r'\s*\n\s*|\s*•\s*|\s{2,}|\t', original_text)

    # Regex
    name_pattern = re.compile(r"^\s*[-•—–‐‑\xad‒–−]?\s*(.+)$")

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        # Match the name pattern
        match = name_pattern.match(token)
        if match:
            name_content = match.group(1)
            name = etree.SubElement(matched_names, "name")
            name.text = name_content
        else:
            print(f"No match for token: {token}")  # Debugging output

# 'd:Namestoremove' elements
def names_to_remove(element, parent, namespaces):
    # Create the container element for 'names-to-remove'
    container_element = etree.SubElement(parent, "names-to-remove")

    # Check if the element has the attribute m:null set to 'true'
    if element.get(f"{{{namespaces['m']}}}null") == 'true':
        container_element.text = "None."
        return

    # Otherwise, process the element content
    original_text = element.text.strip() if element.text else ""
    original_string = etree.SubElement(container_element, "original-string")
    original_string.text = original_text

    # Create 'matched-names' element
    matched_names = etree.SubElement(container_element, "matched-names")

    # Check if the original text matches the tokenization pattern
    if re.search(r'\n|,| and | &amp;', original_text):
        # Tokenize the text using the specified delimiters
        tokens = re.split(r'\n|,| and | &amp;', original_text)
        for token in tokens:
            name = etree.SubElement(matched_names, "name")
            name.text = token.strip()  # Normalize space by stripping
    else:
        # If no delimiters are found, output the original text as a single name
        name = etree.SubElement(matched_names, "name")
        name.text = original_text

# 'd:PPU_x002d_omitfromreport' elements
def omit_from_report(element, parent):
    omit_element = etree.SubElement(parent, "omit-from-report")
    omit_element.text = element.text if element.text else ""

# 'd:Comments' elements
def comments(element, parent, namespaces):
    # Skip the element if it has the 'm:null' attribute
    if element.get(f"{{{namespaces['m']}}}null"):
        return

    # Find the 'dashboard-id' from the following sibling 'd:ID'
    dashboard_id = element.getnext().text if element.getnext() is not None else None

    # Create the 'comments' element with 'dashboard-id' attribute
    comments_element = etree.SubElement(parent, "comments")
    if dashboard_id:
        comments_element.set("dashboard-id", dashboard_id)

    # Check if the text contains newlines to determine paragraph splitting
    original_text = element.text.strip() if element.text else ""
    if '\n' in original_text:
        # Split the text by newline and create a <p> for each line
        lines = re.split(r'\n', original_text)
        for line in lines:
            p_element = etree.SubElement(comments_element, "p")
            p_element.text = line.strip()  # Normalize spaces by stripping
    else:
        # Otherwise, create a single <p> with the entire content
        p_element = etree.SubElement(comments_element, "p")
        p_element.text = original_text

# Extract 'feed/updated' date
updated_element = xml_tree.find(".//atom:updated", namespaces=namespaces)
if updated_element is not None:
    updated_date = datetime.fromisoformat(updated_element.text)
    formatted_date = updated_date.strftime("%B %d, %H:%M")
    downloaded = etree.SubElement(root, "downloaded")
    downloaded.text = formatted_date

# Apply templates to all elements matching 'feed', 'entry', or 'content'
for element in xml_tree.xpath("//feed | //entry | //content"):
    apply_templates(element, root)

# Process 'm:properties' content
for element in xml_tree.xpath("//m:properties", namespaces=namespaces):
    m_properties(element, root, namespaces)

# Tree to string
output_xml = etree.tostring(root, pretty_print=True, encoding="UTF-8").decode("utf-8")

# Save intermediate XML
output_file = 'output.xml'
with open(output_file, 'w', encoding='utf-8') as file:
    file.write(output_xml)
print(f"Saved to: {output_file}")

# B - post-processing for HTML report
