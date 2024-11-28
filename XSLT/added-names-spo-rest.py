import re
import sys
from lxml import etree
from datetime import datetime

def main(input_path, output_path):
    # Parse the input XML
    xml_tree = etree.parse(input_path)

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
                amendments(child, item)
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

    # 'd:Amendments' element including regex patterns and logic from the XSLT
    def amendments(element, parent):
        # Create the 'numbers' element
        numbers = etree.SubElement(parent, "numbers")

        # Normalize and store the original text
        original_text = element.text.strip() if element.text else ""
        original_string = etree.SubElement(numbers, "original-string")
        original_string.text = original_text

        # Create 'matched-numbers' element
        matched_numbers = etree.SubElement(numbers, "matched-numbers")

        # Tokenize based on delimiters: newline, comma, semicolon, "and", and "&amp;"
        tokens = re.split(r'[\n,;]+|\b(?:and|&amp;)\b', original_text)

        # Define regex patterns to match various number formats
        nc_pattern = re.compile(r'NC\d+')  # Matches NC-prefixed numbers
        number_pattern = re.compile(r'^\d+$')  # Matches plain numbers

        # Process each token to create <amd-no> elements or handle unmatched content
        unmatched_tokens = []  # Collect unmatched tokens for 'unmatched-numbers-etc'

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            # Match NC-prefixed numbers
            if nc_pattern.fullmatch(token):
                amd_no = etree.SubElement(matched_numbers, "amd-no")
                amd_no.text = token
            # Match plain numbers
            elif number_pattern.fullmatch(token):
                amd_no = etree.SubElement(matched_numbers, "amd-no")
                amd_no.text = token
            else:
                # Collect unmatched tokens
                unmatched_tokens.append(token)

        # Add unmatched tokens to 'unmatched-numbers-etc'
        if unmatched_tokens:
            unmatched_numbers = etree.SubElement(numbers, "unmatched-numbers-etc")
            unmatched_numbers.text = ", ".join(unmatched_tokens)

        return numbers

    # Print the generated XML for review
    print(etree.tostring(root, pretty_print=True).decode("utf-8"))

    def names(element, parent, namespaces):
        # Create the container element for 'names-to-add'
        container_element = etree.SubElement(parent, "names-to-add")

        # Extract and normalize the original text
        original_text = element.text.strip() if element.text else ""
        original_string = etree.SubElement(container_element, "original-string")
        original_string.text = original_text

        # Create 'matched-names' element
        matched_names = etree.SubElement(container_element, "matched-names")

        # Check if the text contains any of the delimiters
        if re.search(r'\n|,| and | &amp;', original_text):
            # Tokenize the text using the specified delimiters
            tokens = re.split(r'\n|,| and | &amp;', original_text)
            for token in tokens:
                token = token.strip()
                if not token:
                    continue

                # Regex pattern to match and remove prefixes
                name_pattern = re.compile(r"^\s*[\u2022\u002d\u2014\u2015\u2010\u2011\u00ad\u2012\u2013\u2212]?\s*(.+[^ MP])")

                match = name_pattern.match(token)
                if match:
                    name_content = match.group(1)
                    name = etree.SubElement(matched_names, "name")
                    name.text = name_content
                else:
                    print(f"No match for token: {token}")  # Debugging output
        else:
            # If no delimiters are found, create a single 'name' element with normalized text
            name = etree.SubElement(matched_names, "name")
            name.text = original_text

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

        # Find the 'dashboard-id' from the sibling 'd:Id' element
        dashboard_id_element = element.find(f"../d:Id", namespaces)
        dashboard_id = dashboard_id_element.text if dashboard_id_element is not None else None

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
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(output_xml)
    print(f"Saved to: {output_path}")

# Entry point
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python added-names-spo-rest.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    main(input_file, output_file)