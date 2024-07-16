"""
This module contains configuration settings for the sherlock claude application. 
and sets default behaviour

It loads environment variables and defines constants used throughout the application,
including API settings and model parameters.
"""

import os
from dotenv import load_dotenv
import sys
import traceback

def setup_exception_handler():

    def exception_handler(exc_type, exc_value, exc_traceback):
        print("An uncaught exception occurred:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler

def _numbered_dir(base_path='.'):
    """
    Creates a new numbered directory with a prefix.
    
    :param base_path: The base path where the numbered directories will be created.
    :return: The path of the newly created directory.
    """
    # Ensure the base path exists
    os.makedirs(os.path.dirname(base_path), exist_ok=True)

    # Get the prefix from the base_path
    prefix = os.path.basename(base_path)
    parent_dir = os.path.dirname(base_path)
    
    # Get a list of existing numbered directories
    existing_dirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d)) and d.startswith(prefix) and d[len(prefix)+1:].isdigit()]
    
    # Find the highest number
    if existing_dirs:
        highest_num = max(int(d[len(prefix)+1:]) for d in existing_dirs)
    else:
        highest_num = 0
    
    # Create the new directory number
    new_dir_num = highest_num + 1
    new_dir_name = f'{prefix}_{new_dir_num:04d}'  # Format as prefix_XXXX
    
    # Create the new directory
    new_dir_path = os.path.join(parent_dir, new_dir_name)
    os.makedirs(new_dir_path)
    
    return new_dir_path

SHERLOCK_FILEMODE = False
SHERLOCK_LOGMODE  = False

def _set_filemode():

    global SHERLOCK_FILEMODE

    SHERLOCK_FILEMODE=os.getenv("SHERLOCK_FILEMODE")

    if not SHERLOCK_FILEMODE:
        return

    SHERLOCK_FILEMODE = _numbered_dir(SHERLOCK_FILEMODE)
    return SHERLOCK_FILEMODE

def _set_logmode():

    global SHERLOCK_LOGMODE

    SHERLOCK_LOGMODE=os.getenv("SHERLOCK_LOGMODE")

    if not SHERLOCK_LOGMODE:
        return

    SHERLOCK_LOGMODE = _numbered_dir(SHERLOCK_LOGMODE)
    return SHERLOCK_LOGMODE
    
"""str: log steps to sherlock_logmode directory"""


setup_exception_handler()

# Load environment variables from .env file
load_dotenv()

_set_logmode()
_set_filemode()

SHERLOCK_DEBUG = os.getenv("SHERLOCK_DEBUG")
"""str: run in debug mode..."""

SHERLOCK_LITE_DEBUG = os.getenv("SHERLOCK_LITE_DEBUG")
"""str: run in lite debug mode..."""

# Anthropic API settings
API_KEY = os.getenv("ANTHROPIC_API_KEY")
"""str: The Anthropic API key for authentication, loaded from the ANTHROPIC_API_KEY environment variable."""

API_URL = "https://api.anthropic.com/v1/messages"
"""str: The URL for the Anthropic API endpoints."""

ANTHROPIC_VERSION = "2023-06-01"
"""str: The version of the Anthropic API to use in requests."""

# Model settings
MODEL = "claude-3-haiku-20240307"
"""str: The specific model version used for generating responses."""

MAX_TOKENS = 2048
"""int: The maximum number of tokens allowed in the API response."""
