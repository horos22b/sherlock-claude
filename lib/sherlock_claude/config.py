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

setup_exception_handler()

# Load environment variables from .env file
load_dotenv()

SHERLOCK_LOGMODE=os.getenv("SHERLOCK_LOGMODE")
"""str: log steps to sherlock_logmode directory"""

SHERLOCK_FILEMODE=os.getenv("SHERLOCK_FILEMODE")
"""str: interact with claude via the sherlock_filemode directory"""

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
