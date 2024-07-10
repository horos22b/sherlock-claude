"""
This module provides utility functions for file handling, logging, and content processing.

It includes functions for loading JSON files, encoding images, and processing content
with embedded image tags.
"""

import logging
import json
import re
import base64
import os
import inspect
from sherlock_claude.config import SHERLOCK_LITE_DEBUG

base64_image_pattern = re.compile(r'(?:iV)[A-Za-z0-9+/=]{40,}')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        caller_frame = current_frame.f_back
        caller_info = inspect.getframeinfo(caller_frame)
        
        # Extract the short file name and line number
        file_name = os.path.basename(caller_info.filename)
        line_number = caller_info.lineno
        
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
