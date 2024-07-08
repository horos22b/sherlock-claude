"""
This module defines the Investigator class, which represents an AI agent
responsible for analyzing and solving detective cases.

The Investigator interacts with the case data, processes clues, and formulates
theories based on the information provided.
"""

from sherlock_claude.claude_bot import ClaudeBot
from sherlock_claude.case_loader import CaseLoader

import json
import re

class Investigator(ClaudeBot):

    """
    An AI agent that investigates and attempts to solve detective cases.

    This class extends the ClaudeBot base class, adding specific functionality
    for case analysis, clue processing, and theory formulation.

    Attributes:
        setup (dict): The initial setup information for the case.
        questions (list): The list of questions to be answered about the case.
        informants (dict): Information about special investigation spots.
    """

    def __init__(self, case_directory):

        """
        Initialize a new Investigator instance.

        Args:
            case_directory (str): The directory containing the case files.
        """
        system_message = "You are an investigator trying to solve a case. You will receive information about the case, including textual clues and visual evidence. You should formulate theories, ask questions, and try to solve the case. You can also request to review newspapers in bulk at any time."
        super().__init__("investigator", system_message)
        
        self.setup, _, self.questions, _, _, self.informants, _ = CaseLoader.load_case(case_directory)
        self.case_information = {
            "setup": self.setup,
            "questions": self.questions,
            "informants": self.informants,
            "clues": [],
            "newspapers": None,
        }
        
        initial_message = self._create_initial_message()
        self.get_response(initial_message)

    def _create_initial_message(self):
        """
        Create the initial message for the investigator with case setup information.

        Returns:
            str: A formatted string containing the initial case information.
        """
        return f"""Here's the initial case information:

Setup: {json.dumps(self.setup, indent=2)}

Questions to solve: {json.dumps(self.questions, indent=2)}

You also have knowledge of these informants:
{json.dumps(self.informants, indent=2)}

You can request to review newspapers at any time by stating "I would like to review the newspapers."

Based on this information, what are your initial thoughts? Consider if any of the informants might be relevant to contact first, or if you'd like to review the newspapers."""

    def analyze_case(self):
        """
        Analyze the current state of the case and formulate next steps.

        Returns:
            str: The investigator's analysis and proposed next steps.
        """
        prompt = self._create_analysis_prompt()
        return self.get_response(prompt)

    def _create_analysis_prompt(self):
        """
        Create a prompt for case analysis based on current case information.

        Returns:
            str: A formatted string containing the current case information and analysis instructions.
        """
        return f"""Here's a summary of all the information you have gathered so far about the case:

Setup: {json.dumps(self.case_information['setup'], indent=2)}

Questions to solve: {json.dumps(self.case_information['questions'], indent=2)}

Informants: {json.dumps(self.case_information['informants'], indent=2)}

Clues discovered:
{json.dumps(self.case_information['clues'], indent=2)}

Newspapers reviewed: {"Yes" if self.case_information['newspapers'] else "No"}

Based on all this information, what are your current thoughts on the case? 

Where would you like to investigate next? 

Consider the clues you've received, the informants you know about, and the option to review newspapers (if you haven't already). If you think an informant might be relevant, explicitly mention their name in your response. If you want to review the newspapers and haven't done so yet, state "I would like to review the newspapers."

Remember to keep the initial setup and questions in mind as you formulate your thoughts and next steps."""

    def process_clue(self, clue):
        """
        Process a new clue and add it to the case information.

        Args:
            clue (dict): The clue to process.
        """
        self.case_information['clues'].append(clue)

    def process_newspapers(self, newspapers):
        """
        Process the bulk newspaper data.

        This method generates a prompt summarizing the case information,
        including the initial setup, questions to answer, special investigation
        spots, and any gathered evidence. It then sends this prompt to the
        Claude API to get the investigator's analysis and next steps.

        Args:
            newspapers (list): A list of newspaper articles.

        Returns:
            str: The investigator's analysis of the newspaper articles.
        """
        self.case_information['newspapers'] = newspapers
        newspapers_json = json.dumps(newspapers, indent=2)
        prompt = f"""You have received the following newspaper articles in bulk:

{newspapers_json}

Please review these articles carefully and identify any information that might be relevant to the case. Consider how this information relates to the clues you've already gathered and the questions you need to answer. What new insights or theories can you formulate based on this information?

Provide a summary of your findings and how they impact your understanding of the case."""

        return self.get_response(prompt)

    def get_response(self, prompt, images=None):
        """
        Get a response from the AI, including all gathered case information.

        Args:
            prompt (str): The prompt to send to the AI.
            images (list, optional): A list of images to include in the request.

        Returns:
            str: The AI's response.
        """
        full_prompt = f"""Case Information:
{json.dumps(self.case_information, indent=2)}

Current Prompt:
{prompt}"""

        return super().get_response(full_prompt, images)
