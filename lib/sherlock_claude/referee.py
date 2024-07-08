"""
This module defines the Referee class, which manages the flow of the investigation
and provides clues to the Investigator based on their current progress.

The Referee has full knowledge of the case and guides the investigation by
selecting and presenting relevant clues.
"""

from sherlock_claude.claude_bot import ClaudeBot
from sherlock_claude.case_loader import CaseLoader
from sherlock_claude.utils import logger

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
        returned_newspapers (set): A set of indices of newspapers already provided to the Investigator.
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
        self.returned_newspapers = set()

        initial_message = self._create_initial_message()
        self.get_response(initial_message)

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
        
        images = re.findall(r'data:image/[^;]+;base64,[^"]+', clue['description'])
        
        for _ in range(3):  # Try up to 3 times
            response = self.get_response(prompt, images=images)
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
        return f"""Based on the investigator's statement: '{investigator_statement}', 
        rank the following clue on a scale of 1-100 based on how relevant and helpful 
        it would be to the investigator right now. Higher scores mean more relevant. 
        Provide the score and a brief explanation of why you gave that score.
        
        If the investigator's statement mentions a special investigation spot that matches 
        this clue's location exactly, give it a score of 100.
        
        Clue to rank:
        {json.dumps(clue, indent=2)}
        
        Format your response as a JSON object with the following structure:
        {{
            "index": {index},
            "score": <score>,
            "explanation": "<explanation>"
        }}
        """

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
                response = f"Based on your current line of inquiry, I think you should investigate {best_clue['location']}. "\
                           f"Here's what you find:\n\n{best_clue['description']}"
                
                response += f"\n\nRelevance: {clue['explanation']}"
                return response

        return "Think of a different way around the case. You have already seen the most relevant clues here."

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

        total_score = 0
        evaluation_results = []

        for i, (question, answer) in enumerate(zip(self.questions, self.answers)):
            investigator_answer = investigator_answers['answers'][i]
            
            prompt = self._create_evaluation_prompt(question, answer, investigator_answer)
            response = self.get_response(prompt)
            try:
                result = json.loads(response)
                result['question'] = question['question']
                result['points'] = question['points']
                
                result['score'] = min(result['score'], question['points'])
                
                evaluation_results.append(result)
                total_score += result['score']
            except json.JSONDecodeError:
                logger.error(f"Failed to parse referee's evaluation for question {i+1}")

        final_evaluation = {
            "individual_evaluations": evaluation_results,
            "total_score": total_score
        }

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
        return self.newspapers['description']

    def ask_for_solution(self):
        """
        Generate a prompt asking the investigator for their final solution to the case.

        Returns:
            str: A formatted string containing the prompt for the final solution.
        """
        return f"""The investigation is now complete. Based on all the evidence you've gathered, 
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
