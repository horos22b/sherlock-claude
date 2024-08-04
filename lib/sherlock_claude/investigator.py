"""
This module defines the Investigator class, which represents an AI agent
responsible for analyzing and solving detective cases.

The Investigator interacts with the case data, processes clues, and formulates
theories based on the information provided.
"""

from sherlock_claude.claude_bot import ClaudeBot
from sherlock_claude.case_loader import CaseLoader
from sherlock_claude.utils import debug_print, eval_json, ret_json, fix_json, put_latest_file
from sherlock_claude.config import SHERLOCK_FILEMODE, SHERLOCK_LOGMODE

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

    def __init__(self, case_directory, referee):
        system_message = "You are an investigator trying to solve a case. You will receive information about the case, including textual clues and references to visual evidence. You should formulate theories, ask questions, and try to solve the case. You can also request to review newspapers in bulk at any time."

        """
        Initialize a new Investigator instance.

        Args:
            case_directory (str): The directory containing the case files.
        """
        super().__init__("investigator", system_message, case_directory)
        
        self.latest_clue = ''

        self.setup, _, self.questions, _, _, self.informants, _ = CaseLoader.load_case(case_directory)

        self.case_information = {
            "setup": self.setup,
            "questions": self.questions,
            "informants": self.informants,
            "clues": [],
            "clue_path" : [],
            "newspaper_clues": []
        }

        self.newspaper_review_count = 0
        self.max_newspaper_reviews  = 50
        self.referee = referee
        
        initial_message = self._create_initial_message()
        self.get_response(initial_message, dryrun=True)

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

Image references are provided as [IMAGE:X] where X is the image index. You can ask for more information about a specific image by mentioning its index.

Based on this information, what are your initial thoughts? Consider if any of the informants might be relevant to contact first, or if you'd like to review the newspapers."""

    def analyze_case(self, _iter=False):
        """
        Analyze the current state of the case and formulate next steps.
    
        This method generates a prompt summarizing the current case information,
        including the initial setup, questions to answer, informants, clues discovered,
        and newspaper clues. It then sends this prompt to the Claude API to get the
        investigator's analysis and proposed next steps.
    
        Returns:
            str: The investigator's analysis and proposed next steps.
        """
        prompt  = self._create_analysis_prompt()

        if SHERLOCK_FILEMODE or SHERLOCK_LOGMODE:

            explanation_prompt = prompt + self._create_explanation_prompt()

            response = self.get_retry_simple_response(explanation_prompt,filemode=SHERLOCK_FILEMODE,logmode=SHERLOCK_LOGMODE)

            put_latest_file(SHERLOCK_LOGMODE or SHERLOCK_FILEMODE, "analysis", response, prettify=True )


        prompt += self._create_pick_prompt()

        if SHERLOCK_FILEMODE and _iter and _iter > 0:

            next_clue = self.get_latest_clue()
            debug_print("Investigator", f"next clue: {next_clue}")

            prompt = f"\n-----\nnext clue\n----\n{next_clue}\n"
            prompt += self._create_pick_prompt()

            response = self.get_retry_simple_response(prompt,filemode=SHERLOCK_FILEMODE)

        else:
            debug_print("Investigator", f"inital prompt: {prompt}")
            response = self.get_retry_simple_response(prompt,filemode=SHERLOCK_FILEMODE, logmode=SHERLOCK_LOGMODE)

        debug_print("Investigator", f"initial response: {response}")

        return(response)

    def final_theory(self):

        """
        Generate the final theory for the case based on all gathered information.
    
        This method creates a prompt that includes all the case information and asks
        for a final theory on the case. It then sends this prompt to the Claude API
        to get the investigator's final theory.
    
        Returns:
            str: The investigator's final theory on the case.
        """

        prompt  = self._create_analysis_prompt()
        prompt += self._create_final_theory_prompt()

        if SHERLOCK_FILEMODE:
            debug_print("Investigator", f"final theory prompt: {prompt}")
            prompt = self._create_final_theory_prompt()
            response = self.get_retry_simple_response(prompt,filemode=SHERLOCK_FILEMODE)
            debug_print("Investigator", f"final theory response: {response}")

        else:
            debug_print("Investigator", f"final theory prompt: {prompt}")
            response = self.get_retry_simple_response(prompt,filemode=SHERLOCK_FILEMODE,logmode=SHERLOCK_LOGMODE)
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

Consider the clues you've received, the informants you know about, and the option to review newspapers (if you haven't already). If you think an informant might be relevant, explicitly mention their name in your response. If you want to review the newspapers, state "I would like to review the newspapers." When deciding whether or not to retain a clue from the newspapers, please review the current newspaper clues that you have and only decide to catalog new clues.

Also remember that you are playing a GAME. The solution of the puzzle in the game is bounded by the information present in the clues OF the game. Therefore it is likely that the solution will be something that makes sense to integrate disparate parts of clues that you find. Making suppositions which aren't supported by what you have found is likely to be incorrect, the suspects in the case for example are bounded to person or persons that are in the story itself.

Likewise the solution is likely to feel complete, to drive a narrative based off of the clues that you see. When there are multiple possible options, the likely solution is due to some specific forensic detail that only matches a certain theory. Comparing and contrasting different theories should start by trying to reconcile those theories with corroborating evidence, namely evidence showing means, motive and opportunity, or physical evidence pointing to a specific theory. Likewise, please try to connect the crime or crimes to the people who you posit committed it by reflecting on how that crime might relate to their background or skillset.

Also, remember to keep the initial setup and questions in mind as you formulate your thoughts and next steps.
"""

    def _create_explanation_prompt(self):

        return """
Please consider the evidence so far and formulate your theories. What do you think is going on? What are the motives behind the case? What is the supporting evidence you have for your theories? What is contradicting evidence that you have to consider? How confident are you in these findings? What are some alternate theories you need to track down?

Also, please consider and give your best answer for the questions that were given.
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
        # If there are any [IMAGE:X] references in the clue, you can add:
        # You can ask for more details about any image by mentioning its index.

        self.case_information['clues'].append(clue)
        self.latest_clue = clue

        debug_print("Investigator", f"clue path: {json.dumps(self.case_information['clue_path'])}")
        debug_print("Investigator", f"next clue: {self.case_information['clues'][-1]}")


    def process_newspapers_2(self, newspapers):

        """
        Process the bulk newspaper data.

        This method generates a prompt summarizing the case information,
        including the initial setup, questions to answer, special investigation
        spots, and any gathered evidence. It then sends this prompt to the
        Claude API to get the investigator's analysis of the newspaper articles.

        Args:
            newspapers (list): A list of newspaper articles.

        Returns:
            dict: The investigator's analysis of the newspaper articles, containing
                  'description', 'relevance', and 'explanation' keys.
        """

        def eval_json(json_string, key):

            json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, re.DOTALL)

            if not json_string:
                return False

            try:
                _json = fix_json(json_string.group(1))
                json.loads(_json)

                return True
            except json.JSONDecodeError:
                return False

        def ret_json(json_string, key):

            json_string = re.search(r'({[^}]+"%s"\s*:[^}]+})' % key, json_string, re.DOTALL).group(1)
            _json = fix_json(json_string)

            return json.loads(_json)

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

        if SHERLOCK_FILEMODE:
            response = self.get_retry_simple_response(prompt, lambda x: eval_json(x, 'description'), lambda x: ret_json(x, 'description'), filemode=SHERLOCK_FILEMODE)
        else:
            response = self.get_retry_simple_response(init_prompt + prompt, lambda x: eval_json(x, 'description'), lambda x: ret_json(x, 'description'), logmode=SHERLOCK_LOGMODE)



        debug_print("Investigator", f"found the following clues in the newspaper: {response}")

        self.case_information['newspaper_clues'].append(response)

        self.latest_clue = response

    def process_newspapers(self, newspapers):
        self.newspaper_review_count += 1
        if self.newspaper_review_count > self.max_newspaper_reviews:
            return {"description": "You have reached the maximum number of newspaper reviews."}

        self.case_information['newspapers'] = newspapers
        newspapers_json = json.dumps(newspapers, indent=2)

        prompt = f"""
Given all of the information you know about the case and your current theories and observations, carefully review the following newspaper text.
This is a data dump of information, some relevant to the case at hand, most irrelevant.

Analyze the content and identify the single most important and relevant clue you haven't cataloged before. Provide:

1. A brief description of the clue
2. Its relevance to the case
3. Your rationale for considering it important

Remember to compare this potential new clue with the ones you've already cataloged to avoid duplication.

Format your response as a JSON object with the following structure:
{{
    "description": "<clue description>",
    "relevance": "<clue relevance>",
    "rationale": "<your rationale>"
}}

Here are your existing newspaper clues for reference:
{json.dumps(self.case_information['newspaper_clues'], indent=2)}

NEWSPAPER DATA:
{newspapers_json}
"""

        response = self.get_retry_simple_response(
            self._create_analysis_prompt() + prompt,
            lambda x: eval_json(x, ['description', 'relevance', 'rationale']),
            lambda x: ret_json(x, ['description', 'relevance', 'rationale']),
            logmode=SHERLOCK_LOGMODE
        )

        debug_print("Investigator", f"Found the following clue in the newspaper: {json.dumps(response, indent=2)}")

        # Check if the new clue is sufficiently different from existing clues
        if self._is_new_clue(response):
            self.case_information['newspaper_clues'].append(response)
            put_latest_file(SHERLOCK_LOGMODE or SHERLOCK_FILEMODE, "newspaper", response, prettify=True )
            debug_print("Investigator", "Added new clue to newspaper clues.")
        else:
            debug_print("Investigator", "Clue was too similar to existing clues. Not added.")

        return response

    def _is_new_clue(self, new_clue):
        for existing_clue in self.case_information['newspaper_clues']:
            if self._clue_similarity(new_clue, existing_clue) > 0.7:  # Adjust this threshold as needed
                return False
        return True

    def _clue_similarity(self, clue1, clue2):
        similarity = self.referee.compare_clues(clue1, clue2)
        return similarity

    def get_latest_clue(self):

        return self.latest_clue

    def answer_questions(self):

        """
        Provide final answers to the case questions based on the investigation.
    
        This method generates a prompt for each question in the case, including all
        the evidence gathered during the investigation. It then sends these prompts
        to the Claude API to get the investigator's final answers and confidence levels.
    
        Returns:
            dict: A dictionary containing the answers to each question and the 
                  investigator's confidence level for each answer.
        """

        questions = self.case_information['questions']
        answers = []


        for question in questions:
            prompt = f"""Based on all the evidence you've gathered during the investigation, please answer the following question for {question['points']} points:

{question['question']}

Provide your answer and your confidence level. Please limit your answer to the following question and the following question alone.

Format your response as a JSON object with the following structure, where <question> indicates the questions you are going to be answering, <your_answer> indicates the answer you are giving, and <confidence_level> is how confident you are of an answer in the form of a number between 0 and 100:
{{
    "question": "<question>",
    "answer": "<your answer>",
    "confidence": <confidence_level>
}}
"""
            investigation_prompt  = self._create_analysis_prompt()

            if SHERLOCK_FILEMODE:
                response = self.get_retry_simple_response( prompt, lambda x: eval_json(x, 'question'), lambda x: ret_json(x, 'question'), filemode=SHERLOCK_FILEMODE)
            else:
                response = self.get_retry_simple_response( investigation_prompt + prompt, lambda x: eval_json(x, 'question'), lambda x: ret_json(x, 'question'), logmode=SHERLOCK_LOGMODE)

            debug_print("Investigator", f"Question: {question['question']}\nResponse: {response}")
            answers.append(response)
            

        return {"answers": answers}
