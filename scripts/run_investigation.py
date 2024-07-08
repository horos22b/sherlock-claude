#!/usr/bin/env python3

"""
This script is the entry point for running a sherlock claude investigation.

It takes a case directory as a command-line argument, initializes an Investigation
object with the specified case, and runs the investigation process.
"""

import sys
import os

# Add the lib directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib')))

import pdb
pdb.set_trace()
from sherlock_claude.investigation import Investigation

def main():

    """
    The main function that parses command-line arguments and runs the investigation.

    This function expects a single command-line argument specifying the path to
    the case directory. It validates the input, creates an Investigation object,
    and runs the investigation process.

    Usage:
        python run_investigation.py <case_directory>
    """

    if len(sys.argv) != 2:
        print("Usage: python run_investigation.py <case_directory>")
        sys.exit(1)

    case_directory = sys.argv[1]
    if not os.path.isdir(case_directory):
        print(f"Error: {case_directory} is not a valid directory")
        sys.exit(1)

    investigation = Investigation(case_directory)
    investigation.run()

if __name__ == "__main__":
    main()
