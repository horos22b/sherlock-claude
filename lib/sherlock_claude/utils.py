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

    image_tags = re.findall(r'<<(.+?)>>', content)
    for tag in image_tags:
        for ext in ['.jpg', '.png', '.gif']:  # Add more formats if needed
            image_path = os.path.join(case_directory, f"{tag}{ext}")
            if os.path.exists(image_path):
                image_data = load_image(image_path)
                content = content.replace(f"<<{tag}>>", image_data)
                break
        else:
            logger.warning(f"Image not found for tag: {tag}")
    return content
