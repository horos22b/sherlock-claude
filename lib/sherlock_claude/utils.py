"""
This module provides utility functions for file handling, logging, and content processing.

It includes functions for loading JSON files, encoding images, and processing content
with embedded image tags.
"""

import logging
import json
import re
import regex
import base64
import os
import inspect
import glob

from sherlock_claude.config import SHERLOCK_LITE_DEBUG

base64_image_pattern = re.compile(r'(?:iV)[A-Za-z0-9+/=]{40,}')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _std_string(_data):

    if isinstance(_data, str):
        _to_write = _data

    elif isinstance(_data, dict):
        _to_write = _data['messages'][0]['content']

    return _to_write


def fix_json(_text):

    def no_newline(cmd):
        return regex.sub(r'\n', ' ', cmd)

    # Complex regex replacement
    def replace_func(match):

        groups = match.groups()
        return f'{groups[0]}"{groups[1]}"{groups[2]}{groups[3]}{groups[4]}"{no_newline(groups[5])}"{groups[6]}'

    # Remove all double quotes
    _text = _text.replace('"', '')


    _text = _text.replace('\\', '')

    # Remove commas that are immediately followed by non-whitespace
    _text = regex.sub(r'(.),([^\n])', r'\1\2', _text)

    import pdb
    pdb.set_trace()

    _text = regex.sub(r'(\s*)(\S+)(\s*)(:)(\s*)(.*?)(,\s*\n|\n})', replace_func, _text, flags=re.DOTALL)

    return _text


def write_logmode(logmode, req, response):

    _req      = _std_string(req)
    _response = _std_string(response)

    filemode_in = put_latest_file(logmode, "referee", _req )

    logger.info(f"put latest info into {filemode_in}")

    put_latest_file( logmode, "investigator", _response )


def write_filemode(filemode, data):

    _to_write = _std_string(data)

    _infile = put_latest_file(filemode, "referee", _to_write)

    logger.info(f"put latest info into {_infile}")

    ready = input(f"ready to read from claude. Press <return> to continue: ")

    # special for mac, anthropic puts the files here.
    _fname = get_latest_file(f"{os.environ['HOME']}/Downloads/")

    copy_latest_file(filemode, "investigator", _fname)
        
    return gettext(_fname)

def copy_latest_file(directory, prefix, fname):

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Get list of existing files with the given prefix
    existing_files = [f for f in os.listdir(directory) if f.startswith(prefix)]
    
    # Determine the next number
    if existing_files:
        numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_files]
        next_number = max(numbers) + 1
    else:
        next_number = 1
    
    # Create the new filename
    new_filename = f"{prefix}_{next_number:04d}.txt"
    full_path = os.path.join(directory, new_filename)
    
    os.system(f"cp -f '{fname}' {full_path}")


def get_latest_file(directory):

    list_of_files = glob.glob(os.path.join(directory, '*'))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

import os

def put_latest_file(directory, prefix, content, prettify=False):

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Get list of existing files with the given prefix
    existing_files = [f for f in os.listdir(directory) if f.startswith(prefix)]
    
    # Determine the next number
    if existing_files:
        numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_files]
        next_number = max(numbers) + 1
    else:
        next_number = 1
    
    # Create the new filename
    new_filename = f"{prefix}_{next_number:04d}.txt"
    full_path = os.path.join(directory, new_filename)
    
    # Write the content to the new file
    with open(full_path, 'w') as file:
        if prettify:
            if isinstance(content, str):
                file.write(f"{content}")
            else:
                file.write(prettify_json(json.dumps(content, indent=2, ensure_ascii=True)))
        else:
            file.write(f"{content}")

    return full_path

def puttext(file, _str):

    with open(file, 'w') as f:
        f.write(_str)


def gettext(file):

    return open(file, "r").read()

def replace_quote_newlines(text):

    """
    Replace newline characters with '\\n' only within single or double quoted strings.
    
    Args:
        text (str): The input text to process.
    
    Returns:
        str: The processed text with newlines replaced only within quoted strings.
    """

    def replace_newlines(match):
        # Get the quote character used (single or double)
        quote = match.group(1)
        # Get the content of the string
        content = match.group(2)
        # Replace newlines in the content
        content = content.replace('\n', '\\n')
        # Return the string with the original quotes
        return f"{quote}{content}{quote}"

    pattern = r'(["\'"])((?:(?!\1).|\n)*?)\1'

    text = re.sub(r"'", "", text)    
    return re.sub(pattern, replace_newlines, text, flags=re.DOTALL)

def eval_score(response):

    if not eval_json(response, 'score'):
        return False

    dat = ret_json(response, 'score')
    score = int(dat['score'])

    if score is not None and 0 <= score <= 100:
        return True
    return False

def eval_confidence(response):

    if not eval_json(response, 'confidence'):
        return False

    dat = ret_json(response, 'confidence')
    score = int(dat['confidence'])

    if score is not None and 0 <= score <= 100:
        return True

    return False


def eval_json(json_string, key):

    json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, flags=re.DOTALL)

    if not json_string:
        return False

    try:
        _json = json_string.group(1)
        _json = fix_json(_json)

        json.loads(_json)

        return True
    except json.JSONDecodeError:
        return False

def ret_json(json_string, key):

    json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, re.DOTALL).group(1)
    json_string = fix_json(json_string)

    return json.loads(json_string)


def load_json(file_path):

    """
    Load and parse a JSON file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The parsed JSON data.

    Raises:
        FileNotFoundError: If the specified file is not found.
        json.JSONDecodeError: If the file contains invalid JSON.
    """

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"JSON decoding error in file: {file_path}")
        raise

def load_image(file_path):

    """
    Load an image file and encode it as a base64 string.

    Args:
        file_path (str): The path to the image file.

    Returns:
        str: The base64-encoded image data.
    """

    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_content(content, case_directory):

    """
    Process content by replacing image tags with base64-encoded image data.

    This function searches for image tags in the format <<image_name>> and replaces
    them with the corresponding base64-encoded image data.

    Args:
        content (str): The content containing image tags.
        case_directory (str): The directory containing the image files.

    Returns:
        str: The processed content with image tags replaced by base64-encoded image data.
    """

    errors = []

    image_tags = re.findall(r'<<(.+?)>>', content)
    for tag in image_tags:
        for ext in ['', '.jpg', '.png', '.gif']:  # Add more formats if needed
            image_path = os.path.join(case_directory, f"{tag}{ext}")
            if os.path.exists(image_path):
                image_data = load_image(image_path)
                content = content.replace(f"<<{tag}>>", image_data)
                break
        else:
            errors.append(f"Image not found for tag: {tag}")
            logger.error(f"Image not found for tag: {tag}")

    if errors:
        logger.error(f"raising errors")
        raise BaseException("Issues with images\n");

    return content

def summarize_text(text, max_length=100):
    """Summarize text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "... [text truncated]"

def summarize_large_text_blocks(message):
    """Summarize text blocks enclosed in six equal signs."""
    pattern = r'======\n(.*?)\n======'
    
    def replace_func(match):
        text_block = match.group(1)
        summarized = summarize_text(text_block)
        return f"======\n{summarized}\n======"
    
    return re.sub(pattern, replace_func, message, flags=re.DOTALL)

def debug_print(role, message):

    if SHERLOCK_LITE_DEBUG:
        # Get the caller's information
        current_frame = inspect.currentframe()
        excluded_files = [ 'utils.py' ]  # Add files to exclude
        
        while current_frame:
            frame_info = inspect.getframeinfo(current_frame)
            file_name = os.path.basename(frame_info.filename)
            if file_name not in excluded_files:
                break
            current_frame = current_frame.f_back
        
        # Extract the short file name and line number
        line_number = frame_info.lineno
        
        # Create the location string
        location = f"{file_name}:{line_number}"

        # Summarize large text blocks
        message = summarize_large_text_blocks(message)

        # Summarize base64 images
        message = summarize_base64_images(message)

        # Prettify the message
        pretty_message = prettify_json(message)

        header = f"\n{'=' * 20} {role.upper()} ({location}) {'=' * 20}"
        footer = "=" * (44 + len(role) + len(location))
        logger.info(f"{header}\n{pretty_message}\n{footer}")

def prettify_json(message):
    """
    Prettify JSON strings within the message and improve overall readability.
    
    Args:
        message (str): The input message that may contain JSON strings.
    
    Returns:
        str: The prettified message with formatted JSON and improved readability.
    """
    def parse_json(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s

    def parse_json(s):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s

    # Find all JSON-like strings in the message
    json_pattern = r'\{[^{}]*\}'
    json_strings = re.findall(json_pattern, message)

    # Prettify each JSON-like string
    for js in json_strings:
        parsed = parse_json(js)
        if isinstance(parsed, dict):
            pretty = json.dumps(parsed, indent=2)
            message = message.replace(js, pretty)

    # Replace escaped newlines with actual newlines
    message = message.replace('\\n', '\n')
    
    # Remove unnecessary backslashes
    message = re.sub(r'\\(?!["/])', '', message)

    return message

def summarize_large_text_blocks(message):
    """Summarize text blocks enclosed in six equal signs."""
    pattern = r'======\n(.*?)\n======'
    
    def replace_func(match):
        text_block = match.group(1)
        summarized = summarize_text(text_block)
        return f"======\n{summarized}\n======"
    
    return re.sub(pattern, replace_func, message, flags=re.DOTALL)

def find_base64_images(text):
    return base64_image_pattern.findall(text)

# Function to summarize base64 images
def summarize_base64_images(text):
    def replace_image(match):
        image_data = match.group(0)
        return f"[BASE64 IMAGE: {len(image_data)} characters]"
    
    return base64_image_pattern.sub(replace_image, text, re.DOTALL)
