"""
This module provides the CaseLoader class for loading and processing case data.

The CaseLoader is responsible for reading various JSON files that define a case,
including setup, clues, questions, answers, solution, informants, and newspapers.
"""

from sherlock_claude.utils import load_json
from sherlock_claude.image_processor import ImageProcessor

import os

class CaseLoaderError(Exception):
    """Custom exception for CaseLoader errors."""
    pass

class CaseLoader:

    """
    A static class for loading and processing case data from JSON files.
    """

    @staticmethod
    def load_json_file(case_directory, filename):
        """
        Helper function to load a JSON file and handle potential errors.

        Args:
            case_directory (str): The directory containing the case JSON files.
            filename (str): The name of the JSON file to load.

        Returns:
            dict: The loaded JSON data.

        Raises:
            CaseLoaderError: If the file is missing or cannot be loaded.
        """
        file_path = os.path.join(case_directory, filename)
        if not os.path.exists(file_path):
            raise CaseLoaderError(f"Required file '{filename}' is missing from the case directory.")
        
        try:
            return load_json(file_path)
        except Exception as e:
            raise CaseLoaderError(f"Error loading '{filename}': {str(e)}")

    @staticmethod
    def load_case(case_directory):
        """
        Load all components of a case from JSON files in the specified directory.

        This method loads and processes the following JSON files:
        - setup.json: Initial case setup information
        - clues.json: Available clues for the case
        - questions.json: Questions to be answered about the case
        - answers.json: Correct answers to the case questions
        - solution.json: Complete solution for the case
        - informants.json: Information about informants
        - newspapers.json: Newspaper articles related to the case

        Args:
            case_directory (str): The directory containing the case JSON files.

        Returns:
            tuple: A tuple containing (setup, clues, questions, answers, solution, informants, newspapers).

        Raises:
            CaseLoaderError: If any required file is missing or cannot be loaded.
        """

        required_files = [
            'setup.json',
            'clues.json',
            'questions.json',
            'answers.json',
            'solution.json',
            'informants.json',
            'newspapers.json'
        ]

        # Check if all required files exist
        for file in required_files:
            if not os.path.exists(os.path.join(case_directory, file)):
                raise CaseLoaderError(f"Required file '{file}' is missing from the case directory.")
        
        try:
            setup = CaseLoader.load_json_file(case_directory, 'setup.json')
            clues = CaseLoader.load_json_file(case_directory, 'clues.json')
            questions = CaseLoader.load_json_file(case_directory, 'questions.json')
            answers = CaseLoader.load_json_file(case_directory, 'answers.json')
            solution = CaseLoader.load_json_file(case_directory, 'solution.json')
            informants = CaseLoader.load_json_file(case_directory, 'informants.json')
            newspapers = CaseLoader.load_json_file(case_directory, 'newspapers.json')

            # Process content to replace image tags with indexed references

            image_processor = ImageProcessor()
            image_processor.set_case_directory(case_directory)
            
            setup['description'] = image_processor.process_content(setup['description'])
            
            for clue in clues:
                clue['description'] = image_processor.process_content(clue['description'])
            
            newspapers['description'] = image_processor.process_content(newspapers['description'])
            
            # Add the full image index to the setup
            setup['image_index'] = image_processor.get_full_image_index()

        except CaseLoaderError as e:
            raise  # Re-raise the CaseLoaderError
        except Exception as e:
            raise CaseLoaderError(f"Unexpected error loading case: {str(e)}")

        return (
            setup,
            clues,
            questions,
            answers,
            solution,
            informants,
            newspapers
        )

