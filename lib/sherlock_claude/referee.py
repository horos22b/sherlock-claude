"""
This module defines the Referee class, which manages the flow of the investigation
and provides clues to the Investigator based on their current progress.

The Referee has full knowledge of the case and guides the investigation by
selecting and presenting relevant clues.
"""

from sherlock_claude.claude_bot import ClaudeBot
from sherlock_claude.case_loader import CaseLoader
from sherlock_claude.utils import logger, debug_print, eval_json, ret_json, eval_score, eval_confidence
from sherlock_claude.config import SHERLOCK_DEBUG, SHERLOCK_LITE_DEBUG

import json
import re

class Referee(ClaudeBot):

    """
    An AI agent that manages the investigation process and provides clues and newspaper information.

    This class extends the ClaudeBot base class, adding specific functionality
    for clue management, ranking, and evaluation of the Investigator's progress.

    Attributes:
        setup (dict): The initial setup information for the case.
        clues (list): A list of all available clues for the case.
        questions (list): The list of questions to be answered about the case.
        answers (list): The correct answers to the case questions.
        solution_data (dict): The complete solution for the case.
        informants (dict): Information about informants or special investigation spots.
        newspapers (list): Information about newspapers.
        returned_clues (set): A set of indices of clues already provided to the Investigator.
    """

    def __init__(self, case_directory):
        """
        Initialize a new Referee instance.

        Args:
            case_directory (str): The directory containing the case files.
        """
        system_message = "You are a referee in a detective case. You know all the details of the case and will guide an investigator by providing relevant clues and newspaper information based on their current thoughts and questions."
        super().__init__("referee", system_message)
        
        self.setup, self.clues, self.questions, self.answers, self.solution_data, self.informants, self.newspapers = CaseLoader.load_case(case_directory)
        self.returned_clues = set()

        initial_message = self._create_initial_message()
        self.get_response(initial_message, dryrun=True)


    def _create_initial_message(self):
        """
        Create the initial message for the referee with case information.

        Returns:
            str: A formatted string containing the initial case information.
        """
        return f"""Here's the case information:

Setup: {json.dumps(self.setup, indent=2)}

Clues: {json.dumps(self.clues, indent=2)}

Questions to solve: {json.dumps(self.questions, indent=2)}

Case Solution: {json.dumps(self.solution_data, indent=2)}

Informants: {json.dumps(self.informants, indent=2)}
        """

    def rank_single_clue(self, investigator_statement, clue, index):

        """
        Rank a single clue based on its relevance to the investigator's current statement.

        Args:
            investigator_statement (str): The investigator's current analysis or question.
            clue (dict): A dictionary containing clue information.
            index (int): The index of the clue in the clues list.

        Returns:
            dict: A dictionary containing the clue's index, relevance score, and explanation.
        """
        prompt = self._create_ranking_prompt(investigator_statement, clue, index)
        
        for _ in range(3):  # Try up to 3 times

            debug_print("Referee", f"Looking at clue: {json.dumps(prompt)}")

            response = self.get_simple_response(prompt)

            debug_print("Referee", f"Reponse to clue: {json.dumps(response)}")

            try:
                ranked_clue = json.loads(response)
                return ranked_clue
            except json.JSONDecodeError:
                prompt += "\nPlease ensure your response is a valid JSON object."
        
        return {"index": index, "score": 0, "explanation": "Cannot compute"}

    def _create_ranking_prompt(self, investigator_statement, clue, index):
        """
        Create a prompt for ranking a single clue.

        Args:
            investigator_statement (str): The investigator's current analysis or question.
            clue (dict): A dictionary containing clue information.
            index (int): The index of the clue in the clues list.

        Returns:
            str: A formatted string containing the ranking instructions and clue information.
        """
        return f"""
        You are now going to be evaluating the investigator's statement - and trying to match it against a given clue, which contains information on where the clue is and the contents of the clue.

        Your goal is to figure out how close a given clue is on a scale of 0 to 100. If the clue doesn't match the investigator's statement at all, give the clue a 0. If the clue mentions wanting to go to an informant and matches the clue's location exactly, then give that location a 100. I will prefix the investigator's statement with INVESTIGATOR STATEMENT and put it between dashes -------. I will do the same for the clue.

        INVESTIGATOR STATEMENT
        ----------------------
        {investigator_statement} 
        ----------------------

        CLUE TO MATCH INVESTIGATOR STATEMENT WITH
        ----------------------
        {json.dumps(clue, indent=2)}
        ----------------------
 
        Again, please rank the 'INVESTIGATOR STATEMENT' section above with the 'CLUE' section above, on a scale of 1-100 based on how close it matches the 
        investigator's statement.

        Please be discerning and don't make a determination based on how helpful the clue is, 
        this should be based only on the intent of the investigator. It need to discover the clues by itself.
        
        If the investigator's statement mentions a informant spot that matches 
        this clue's location exactly, give it a score of 100.
        
        Finally, Format your response as a JSON object with the following structure, 
        where <score> is the score given and <explanation> is your short explanation:

        {{
            "index": {index},
            "score": <score>,
            "explanation": "<explanation>"
        }}
        """

    def best_choice(self, investigator_response):

        ans = {}

        for next_action in [ "I have enough information solve the case and would like to provide a solution. I don't have any other actions I want to take", "I want to look at the newspapers in my next step of investigation", "I would like to visit an informant in my next step of investigation", "I would like to visit a specific person or place next in my next step of investigation that is not an informant" ]:

            if re.search(r'{[^}]+"next_action"\s*:[^}]+}', investigator_response, re.DOTALL):
                _investigator_next_step = re.search(r'({[^}]+"next_action"\s*:[^}]+})', investigator_response, re.DOTALL).group(1)

            else:
                _investigator_next_step = investigator_response
                logger.warning(f"claude did not provide a json format at the end here: {_investigator_next_step}")
     
            text = f"""
please evaluate the following text, and output a number between 0 and 100 on how close the following text below under the heading 'POTENTIAL ACTION' is to the heading under 'INVESTIGATOR PROPOSED NEXT STEP': 

POTENTIAL ACTION
-------
{next_action}

INVESTIGATOR PROPOSED NEXT STEP
-------
{_investigator_next_step}

Phase your response in terms of a number, again between 0 and 100.  

Please be concise in your answer and return only limited explanation of your rationale, and end with the numbered evaluation.

Format the final part of the response as a JSON object with the following structure, with <score> indicating your final score between 0 and 100, and <reason> indicating your reason:

{{
        "score":  <score>,
        "reason": <reason>
}}
"""
            debug_print("Referee", f"Evaluating next action\n{text}")

            response =  self.get_retry_simple_response(text, eval_score, lambda x: ret_json(x, 'score'), print_eval="Referee")
            ans[next_action] = response['score']

        _max_act = 0
        for key in ans:
            if ans[key] > _max_act:
                _max_act = ans[key]
                _ret_key =  key

        debug_print("Referee", f"Evaluation hash:\nwinning key - '{_ret_key}' - eval hash - {json.dumps(ans,indent=2)}")

        return _ret_key


    def rank_clues(self, investigator_statement):

        """
        Rank all available clues based on their relevance to the investigator's current statement.

        Args:
            investigator_statement (str): The investigator's current analysis or question.

        Returns:
            list: A list of dictionaries containing ranked clue information.
        """

        return [self.rank_single_clue(investigator_statement, clue, index) 
                for index, clue in enumerate(self.clues)]

    def provide_best_clue(self, investigator_statement):

        """
        Provide the most relevant clue to the investigator based on their current statement.

        This method ranks all available clues, selects the highest-ranked clue that hasn't
        been provided yet, and returns it to the investigator.

        Args:
            investigator_statement (str): The investigator's current analysis or question.

        Returns:
            str: A string containing the best clue and its relevance explanation.
        """

        ranked_clues = self.rank_clues(investigator_statement)
        if not ranked_clues:
            return "Cannot find a relevant clue here, please think and try again."
        
        sorted_clues = sorted(ranked_clues, key=lambda x: x['score'], reverse=True)
        
        for clue in sorted_clues:
            if clue['index'] not in self.returned_clues:
                self.returned_clues.add(clue['index'])
                best_clue = self.clues[clue['index']]

                if 'location' in best_clue:
                    _location = best_clue['location']
                    _type = 'location'
                else:
                    _location = best_clue['informant']
                    _type = 'informant'
   
                response = f"\n-------\nBased on your current line of inquiry, you investigate {_location}. "\
                           f"\n-------\nHere's what you find:\n--------\n\n{best_clue['description']}"
                
                debug_print("Referee", f"Providing best clue:\n{response}")
                return { 'type': _type, 'location': _location, 'description' : response }

        debug_print("Referee", f"think of a different way around the case. You have already seen the most relevant clues here.")

        return { 'type': 'dead_end', 'location':  'none', 'description':  "Think of a different way around the case. You have already seen the most relevant clues here." }

    def evaluate_answer(self, investigator_answers):

        """
        Evaluate the investigator's final answers to the case questions.

        This method compares the investigator's answers to the correct answers,
        provides a detailed evaluation, and calculates a score for each question.

        Args:
            investigator_answers (dict): A dictionary containing the investigator's answers and confidence levels.

        Returns:
            str: A JSON string containing the evaluation results and total score.
        """

#        import pdb
#        pdb.set_trace()

        total_score = 0
        evaluation_results = []

        for i, (question, answer) in enumerate(zip(self.questions, self.answers)):
            investigator_answer = investigator_answers['answers'][i]
        
            prompt = self._create_evaluation_prompt(question, answer, investigator_answer)
            debug_print("Referee", f"Final evaluation:\n{prompt}")

            result =  self.get_retry_simple_response(prompt, eval_confidence, lambda x: ret_json(x, 'confidence'), print_eval="Referee")
            debug_print("Referee", f"Final evaluation for question {i+1}:\n{result}")

            result['question'] = question['question']
            result['points'] = question['points']
                
            result['score'] = (result['confidence'] / 100) * question['points']
                
            evaluation_results.append(result)
            total_score += result['score']

        final_evaluation = {
            "individual_evaluations": evaluation_results,
            "total_score": total_score
        }

        debug_print("Referee", f"Final evaluation:\n{json.dumps(final_evaluation, indent=2)}")

        return json.dumps(final_evaluation, indent=2)

    def _create_evaluation_prompt(self, question, answer, investigator_answer):
        """
        Create a prompt for evaluating the investigator's answer to a single question.

        Args:
            question (dict): The question being evaluated.
            answer (str): The correct answer to the question.
            investigator_answer (dict): The investigator's answer and confidence level.

        Returns:
            str: A formatted string containing the evaluation instructions and answer information.
        """
        return f"""Evaluate the following answer:

Question: {question['question']} (Points: {question['points']})
Correct Answer: {answer['answer']}
Investigator's Answer: {investigator_answer['answer']}
Investigator's Confidence: {investigator_answer['confidence']}%

Provide a detailed evaluation, highlighting what the investigator got right and what they missed.
Give an accuracy score from 0 to 100 for this answer, taking into account the confidence level provided by the investigator.
The final score for this question should be the accuracy percentage of the points available for this question, rounded down to the nearest integer. The maximum score cannot exceed the points available for this question.

Format your response as a JSON object with the following structure:
{{
    "evaluation
    "accuracy": <accuracy score between 0 and 100>,
    "score": <final score for this question>
}}
        """


    def _create_evaluation_prompt(self, question, answer, investigator_answer):
        """
        Create a prompt for evaluating the investigator's answer to a single question.

        Args:
            question (dict): The question being evaluated.
            answer (str): The correct answer to the question.
            investigator_answer (dict): The investigator's answer and confidence level.

        Returns:
            str: A formatted string containing the evaluation instructions and answer information.
        """
        return f"""Evaluate the following answer:

Question: {question['question']} (Points: {question['points']})
Correct Answer: {answer}
Investigator's Answer: {investigator_answer['answer']}
Investigator's Confidence: {investigator_answer['confidence']}%

Provide a detailed evaluation, highlighting what the investigator got right and what they missed.
Give an accuracy score from 0 to 100 for this answer, taking into account the confidence level provided by the investigator.
The final score for this question should be the accuracy percentage of the points available for this question, rounded down to the nearest integer. The maximum score cannot exceed the points available for this question.

Format your response as a JSON object with the following structure:
{{
    "evaluation": "<your detailed evaluation>",
    "accuracy": <accuracy score 0-100>,
    "score": <final score for this question>
}}
        """

    def provide_newspapers(self):
        """
        Provide all newspaper articles to the investigator.

        Returns:
            list: A list of all newspaper articles.
        """

        debug_print("Referee", "Providing all newspaper articles.")
        return self.newspapers['description']


    def _create_evaluation_prompt(self, question, answer, investigator_answer):
        return f"""Evaluate the following answer critically:

Question: {question['question']}
Correct Answer: {answer['answer']}
Investigator's Answer: {investigator_answer['answer']}

Case Solution Summary: {self.solution_data['description']}

Provide a detailed critical evaluation of the investigator's answer. Consider the following:

1. How close is the investigator's answer to the correct answer in terms of content and meaning?
2. Are there any partial truths or insights in the investigator's answer?

Note that you are only evaluating how close the investigator's statement is to the TRUTH as given in the correct answer. If they say they do not know or are not confident, then the answer they give is INCORRECT and they should get a low confidence score from you. Be as objective and sincere in your answer as possible here. They are trying to solve the case here your evaluation should only reflect how close they got to doing this.

Note too that you are only evaluation THIS QUESTION and its truth value, not how it reflects on other parts of the case. We will do an overall comparison of the full solution in a different query. If the answer is outright wrong, give them 0 points.

Format your response as a JSON object with the following structure:
{{
    "evaluation": "<your detailed critical evaluation>",
    "confidence": <confidence level 0-100>
}}
        """

    def ask_for_solution(self):
        """
        Generate a prompt asking the investigator for their final solution to the case.

        Returns:
            str: A formatted string containing the prompt for the final solution.
        """

        referee_prompt = f"""The investigation is now complete. Based on all the evidence you've gathered, 
        please provide your final answers to the following questions:

        {json.dumps(self.questions, indent=2)}

        For each question, provide your answer and your confidence level (0-100%).
        Format your response as a JSON object with the following structure:
        {{
            "answers": [
                {{
                    "question": "<question text>",
                    "answer": "<your answer>",
                    "confidence": <confidence level>
                }},
                ...
            ]
        }}
        """

        debug_print("Referee", f"Asking for final solution:\n{referee_prompt}")

        return referee_prompt
