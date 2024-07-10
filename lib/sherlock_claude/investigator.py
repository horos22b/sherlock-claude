"""
This module defines the Investigator class, which represents an AI agent
responsible for analyzing and solving detective cases.

The Investigator interacts with the case data, processes clues, and formulates
theories based on the information provided.
"""

from sherlock_claude.claude_bot import ClaudeBot
from sherlock_claude.case_loader import CaseLoader
from sherlock_claude.utils import debug_print, eval_json, ret_json

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

#        import pdb
#        pdb.set_trace()

        self.case_information = {
            "setup": self.setup,
            "questions": self.questions,
            "informants": self.informants,
            "clues": [],
            "clue_path" : [],
            "newspaper_clues": []
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
        prompt  = self._create_analysis_prompt()
        prompt += self._create_pick_prompt()

        debug_print("Investigator", f"inital prompt: {prompt}")
        response = self.get_retry_simple_response(prompt)
        debug_print("Investigator", f"intiall response: {response}")

        return(response)

    def final_theory(self):

        prompt  = self._create_analysis_prompt()
        prompt += self._create_final_theory_prompt()

        debug_print("Investigator", f"final theory prompt: {prompt}")
        response = self.get_retry_simple_response(prompt)
        debug_print("Investigator", f"final theory response: {response}")

        return(response)
    

    def _parse_investigator_choice(self, response):
        # Logic to determine which of the four choices the investigator has made
        if "I would like to review the newspapers" in response:
            return "read_newspapers"
        elif "I am ready to provide a solution" in response:
            return "provide_solution"
        elif any(informant["informant"] in response for informant in self.case_information["informants"]):
            return "visit_informant", response
        else:
            return "suggest_location", response

    def _create_final_theory_prompt(self):

        """
        Create a prompt for determining final theory based on current case information.

        Returns:
            str: A formatted string containing the investigator's final theory on the matter.
        """

        return """
Given all the information that you have gathered above, Think carefully and determine what do you consider to be the final theory on the case at hand? What are the means, motives, and opportunities of the perpetrators of the given crime or crimes? How do your theories work to explain the evidence of the case at hand? What doubts do you have about your theory and how confident on a scale from 1-100 are you that the theory is correct?

Feel free to elaborate as much as you want about this in your answer.
"""


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

Newspapers clues: {json.dumps(self.case_information['newspaper_clues'])}

Based on all this information, what are your current thoughts on the case? 

Where would you like to investigate next? 

Consider the clues you've received, the informants you know about, and the option to review newspapers (if you haven't already). If you think an informant might be relevant, explicitly mention their name in your response. If you want to review the newspapers and haven't done so yet, state "I would like to review the newspapers."

Remember to keep the initial setup and questions in mind as you formulate your thoughts and next steps.
"""

    def _create_pick_prompt(self):

        return """
IMPORTANT - PLEASE READ WITH HIGHEST PRIORITY. Based on thse insights, respond on how you would like to proceed:

option 1. Review all of the questions above. If you have a high level of confidence that you know the answer to all of these questions, respond with text including the phrase - "provide solution" and indicate to the referee that you are ready to solve it.

option 2. if you aren't ready to solve the case, and you feel that visiting a person or place that has been mentioned in the context above would be most helpful in your investigation, please indicate that you want to visit that person or place next, and mention it by name in your responses.

option 3. if you are not ready to solve the case, and you feel that it is the most hopeful course of action, pick an informant in your list of informants to go to next. Indicate which informant you want to talk to, and the rationale as to why you want to do this.

option 4. if you are not ready to solve the case, and you feel that it is will help the most, say that you want to review the newspapers. Mention that you want to do this and the newspapers surrounding the case will be given to you and you can look through them for clues.

Please respond in the format of a JSON file at the end of your response, where <action> is one of 'provide solution', 'visit informant', 'review newspapers', or 'visit person or place'. If the action is to visit an informant, print the informant name. If the action is to visit a person or place, please mention the person or place in the action. For <reason>, put in the reason why you want to do this.

Also, IMPORTANT, please keep your reply to one option as to where to go to next.

{{
    "next_action": "<action>",
    "reason": "<reason>"
}}
"""



    def process_clue(self, investigator_response, referee_response):

        """
        Process a new clue and add it to the case information.

        Args:
            investigator_response (str): the prompt from the investigator that determined the location.
            referee_response (dict): the clue given to the investigator by the referee.
        """
        self.case_information['clue_path'].append(f"location - {referee_response['location']}, type - {referee_response['type']}") 

        clue = f"""
NEW CLUE GIVEN
----------------- 
location:       {referee_response['location']}
location_type:  {referee_response['type']}
description:    {referee_response['description']}")
"""

        self.case_information['clues'].append(clue)

        debug_print("Investigator", f"clue path: {json.dumps(self.case_information['clue_path'])}")
        debug_print("Investigator", f"next clue: {self.case_information['clues'][-1]}")


    def process_newspapers(self, newspapers):

        def eval_json(json_string, key):

            json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, re.DOTALL).group(1)

            try:
                json.loads(json_string)
                return True
            except json.JSONDecodeError:
                return False

        def ret_json(json_string, key):

            json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, re.DOTALL).group(1)
            return json.loads(json_string)

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

        debug_print("Investigator", f"processing newspapers")

        prompt = f"""
Given all of the above information that you know about the case and the theories and obsservations that you have made, please consider the following newspaper text.
It is a data dump of a lot of information, some relevant to the case at hand, most irrelevant.

Look through it, and after you are done looking through it please return a JSON datastructure with the following elements. 

<found_clue_description> is the most important found clue you have found in the newspaper and its description. 
<found_clue_relevance>   is the relevance of this most important clue
<found_clue_explanation> is your rational as to why you think this is a clue.


{{
    "description" : "<found_clue_description>",
    "relevance"   : "<found_clue_relevance>",
    "explanation" : "<found_clue_explanation>"
}}

Again, please put this JSON datastructure at the end of your response and keep your rationale for it to a minimum. Also please keep your response to one clue that is the most relevant and does not resemble other clues you've seen before. At a later stage you can ask for this newspaper again.

NEWSPAPER DATA BELOW
------
======
{newspapers_json}
======
"""
        debug_print("Referee", f"Provided newspapers: {prompt}")

        init_prompt = self._create_analysis_prompt()

        response = self.get_retry_simple_response(init_prompt + prompt, lambda x: eval_json(x, 'description'), lambda x: ret_json(x, 'description'))

        debug_print("Investigator", f"found the following clues in the newspaper: {response}")

        self.case_information['newspaper_clues'].append(response)

    def answer_questions(self):

        questions = self.case_information['questions']
        answers = []


        for question in questions:
            prompt = f"""Based on all the evidence you've gathered during the investigation, please answer the following question for {question['points']}:

{question['question']}

Provide your answer and your confidence level.
Format your response as a JSON object with the following structure, where <question> indicates the questions you are going to be answering, <your_answer> indicates the answer you are giving, and <confidence_level> is how confident you are of an answer in the form of a number between 0 and 100:
{{
    "question": "<question>",
    "answer": "<your answer>",
    "confidence": <confidence_level>
}}
"""
            investigation_prompt  = self._create_analysis_prompt()

            response = self.get_retry_simple_response( investigation_prompt + prompt, lambda x: eval_json(x, 'question'), lambda x: ret_json(x, 'question'))
            debug_print("Investigator", f"Question: {question['question']}\nResponse: {response}")
            answers.append(response)
            

        return {"answers": answers}
