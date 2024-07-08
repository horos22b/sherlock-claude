
"""
Sherlock Claude Case Converter

This script processes text files containing case information and converts them into
JSON files required by the Sherlock Claude system. It handles multiple input files,
each potentially containing multiple sections, and performs various checks to
ensure the integrity and completeness of the case data.

Usage:
    1. Place this script in the same directory as your case input files and image files.
    2. Run the script: python convert_cases.py

The script will process all .txt files in the current directory and generate
corresponding JSON files for each section.

File Format:
    Each .txt file can contain one or more sections.
    Sections are delimited by '---- SECTION_NAME ----' (in uppercase).
    The content of each section is treated as plain text and will be converted to JSON.

Required sections (across all input files):
    - SETUP
    - CLUES
    - QUESTIONS
    - ANSWERS
    - SOLUTION
    - INFORMANTS
    - NEWSPAPERS

Example input file structure:
    ---- SETUP ----

    We knock at 221B Baker Street, and to our greatest surprise, Holmes himself answers the door...

    ---- CLUES ----

    LOC: 42NW Sherlock Holmes

    Holmes was seen leaving his residence at midnight, carrying a suspicious package.

    LOC: 88SE Olsen residence, Bree Street

    A broken vase was found near the entrance, with traces of blood on the shards, pictured here: <<bloody_picture_vase>>

    ---- QUESTIONS ----

    1. Who committed the crime? (25 points)
    2. What was the murder weapon? (20 points)
    3. What was the motive? (30 points)

    ---- ANSWERS ----

    1. The butler committed the crime. (25 points)
    2. The murder weapon was a candlestick. (20 points)
    3. The motive was financial gain. (30 points)

    ---- SOLUTION ----

    The butler, driven by financial desperation, committed the crime using the candlestick because he was about to be fired by his master that he had served for over thirty years. He waited for..

    ---- INFORMANTS ----

    LOC: 5WC Henry Ellis

    Reporter for the London Times
    Knows about recent events in the city

    LOC: 13SW Scotland Yard

    Have all the reports relating to the investigation

    ---- NEWSPAPERS ----

    LONDON TIMES, March 15, 1895

    MYSTERIOUS MURDER AT BREE STREET
    Last night, a gruesome discovery was made at the residence of...

Image references:
    Images should be referenced in the content using the format <<image_name>>.
    The script will check for the existence of these image files in the same directory.

Error handling:
    The script will exit with an error message if it encounters:
    - Duplicate sections across files
    - Unknown sections
    - Missing required sections
    - Missing referenced image files

Tips:
    - Ensure all required sections are present across your input files.
    - Use the LOC: prefix for locations in CLUES and INFORMANTS sections.
    - For both questions and answers, include the point value in parentheses after each item.
    - Number both questions and answers sequentially.
    - Make sure the point values for questions and answers match for each item.
    - Double-check that all referenced images exist in the directory.
    - Make sure each section is properly delimited with the '---- SECTION_NAME ----' format.
"""

import json
import re
import os
import sys

REQUIRED_SECTIONS = [
    'SETUP',
    'CLUES',
    'QUESTIONS',
    'ANSWERS',
    'SOLUTION',
    'INFORMANTS',
    'NEWSPAPERS'
]

def parse_questions_or_answers(content, is_question=True):
    """
    Parse the QUESTIONS or ANSWERS section content.
    
    Args:
        content (str): The content of the QUESTIONS or ANSWERS section.
        is_question (bool): True if parsing questions, False if parsing answers.
    
    Returns:
        list: A list of dictionaries containing text and point values.
    """
    items = []
    pattern = r'(\d+)\.\s*(.+?)\s*\((\d+)\s*points?\)'
    matches = re.finditer(pattern, content, re.MULTILINE)
    for match in matches:
        item_text = match.group(2).strip()
        points = int(match.group(3))
        item = {("question" if is_question else "answer"): item_text, "points": points}
        items.append(item)
    return items


def parse_flat_file(file_path):
    """
    Parse a flat file into sections.
    
    Args:
        file_path (str): Path to the input file.
    
    Returns:
        dict: A dictionary of section names and their content.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    sections = re.split(r'---- (.+?) ----', content)[1:]
    return {sections[i].strip(): sections[i+1].strip() for i in range(0, len(sections), 2)}

def parse_informants(content):
    """
    Parse the INFORMANTS section content.
    
    Args:
        content (str): The content of the INFORMANTS section.
    
    Returns:
        list: A list of dictionaries containing informant information.
    """
    informants = []
    pattern = r'LOC:\s*(.+?)\n([\s\S]+?)(?=\nLOC:|$)'
    matches = re.finditer(pattern, content)
    for match in matches:
        location = match.group(1).strip()
        description = match.group(2).strip()
        informants.append({"informant": location, "description": description})
    return informants

def parse_clues(content):
    """
    Parse the CLUES section content.
    
    Args:
        content (str): The content of the CLUES section.
    
    Returns:
        list: A list of dictionaries containing clue locations and content.
    """
    clues = []
    pattern = r'LOC:\s*(.+?)\n([\s\S]+?)(?=\nLOC:|$)'
    matches = re.finditer(pattern, content)
    for match in matches:
        location = match.group(1).strip()
        clue_content = match.group(2).strip()
        clues.append({"location": location, "description": clue_content})
    return clues

def check_unknown_sections(all_sections):
    """
    Check if there are any unknown sections in the input files.
    
    Args:
        all_sections (dict): A dictionary of all parsed sections.
    
    Raises:
        SystemExit: If any unknown section is found.
    """
    unknown_sections = set(all_sections.keys()) - set(REQUIRED_SECTIONS)
    if unknown_sections:
        print(f"Error: Unknown sections found: {', '.join(unknown_sections)}")
        sys.exit(1)

def convert_to_json(sections):
    """
    Convert section contents to JSON format.
    
    Args:
        sections (dict): A dictionary of section names and their content.
    
    Returns:
        dict: A dictionary of JSON filenames and their content.
    """
    json_files = {}
    
    for section_name, content in sections.items():
        filename = f"{section_name.lower()}.json"
        if section_name == 'CLUES':
            json_content = parse_clues(content)
        elif section_name == 'QUESTIONS':
            json_content = {"questions": parse_questions_or_answers(content, is_question=True)}
        elif section_name == 'ANSWERS':
            json_content = {"answers": parse_questions_or_answers(content, is_question=False)}
        elif section_name == 'NEWSPAPERS':
            json_content = {"description": content.strip()}
        elif section_name == 'INFORMANTS':
            json_content = parse_informants(content)
        elif section_name == 'SOLUTION':
            json_content = {"description": content.strip()}
        else:  # SETUP
            json_content = {"description": content.strip()}
        
        json_files[filename] = json_content
    
    return json_files

def check_required_sections(all_sections):
    """
    Check if all required sections are present.
    
    Args:
        all_sections (dict): A dictionary of all parsed sections.
    
    Raises:
        SystemExit: If any required section is missing.
    """
    missing_sections = set(REQUIRED_SECTIONS) - set(all_sections.keys())
    if missing_sections:
        print(f"Error: Missing required sections: {', '.join(missing_sections)}")
        sys.exit(1)

def check_image_files(all_sections):
    """
    Check if all referenced image files exist.
    
    Args:
        all_sections (dict): A dictionary of all parsed sections.
    
    Raises:
        SystemExit: If any referenced image file is missing.
    """
    image_tags = re.findall(r'<<(.+?)>>', json.dumps(all_sections))
    missing_images = []
    
    for tag in image_tags:
        image_found = False

        if os.path.exists(f"{tag}"):
            image_found=True
            break

        for ext in ['.jpg', '.png', '.gif']:
            if os.path.exists(f"{tag}{ext}"):
                image_found = True
                break
        if not image_found:
            missing_images.append(tag)
    
    if missing_images:
        print(f"Error: Missing image files: {', '.join(missing_images)}")
        sys.exit(1)

def process_files():
    """
    Process all .txt files in the given directory.
    
    Returns:
        dict: A dictionary of all parsed sections.
    
    Raises:
        SystemExit: If there are duplicate sections across files or unknown sections.
    """
    all_sections = {}

    for filename in os.listdir():
        if filename.endswith(".txt"):
            sections = parse_flat_file(filename)
            
            for section_name, content in sections.items():
                if section_name in all_sections:
                    print(f"Error: Duplicate section '{section_name}' found in {filename}")
                    sys.exit(1)
                else:
                    all_sections[section_name] = content

    check_unknown_sections(all_sections)
    check_required_sections(all_sections)
    check_image_files(all_sections)

    return all_sections

def write_readable_json(data, file_path):
    """
    Write JSON data to a file with readable formatting and preserved newlines.
    
    Args:
        data (dict): The data to be written to JSON.
        file_path (str): The path to the output JSON file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=True, indent=2)

def main():
    """
    Main function to process files and generate JSON output.
    
    """

    all_sections = process_files()
    json_files = convert_to_json(all_sections)
    
    for filename, content in json_files.items():
        write_readable_json(content, filename)
        print(f"Created {filename}")

if __name__ == "__main__":
    main()
