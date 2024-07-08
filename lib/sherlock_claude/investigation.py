"""
This module defines the Investigation class, which orchestrates the entire
sherlock claude process, managing interactions between the Investigator and Referee.

The Investigation class controls the flow of the game, including iterations of
clue provision, analysis, and final evaluation.
"""

from sherlock_claude.referee import Referee
from sherlock_claude.investigator import Investigator
from sherlock_claude.utils import logger

import json

class Investigation:

    """
    A class that manages the overall investigation process.

    This class coordinates between the Investigator and Referee, managing the
    flow of the investigation, including clue provision, analysis, and evaluation.

    Attributes:
        referee (Referee): The Referee instance managing clues and evaluation.
        investigator (Investigator): The Investigator instance analyzing the case.
        max_iterations (int): The maximum number of investigation iterations allowed.
    """

    def __init__(self, case_directory):

        """
        Initialize a new Investigation instance.

        Args:
            case_directory (str): The directory containing the case files.
        """
        self.referee = Referee(case_directory)
        self.investigator = Investigator(case_directory)
        self.max_iterations = 100

    def run(self):

        """
        Run the entire investigation process.

        This method manages the main loop of the investigation, conducting
        iterations until the case is solved or the maximum number of iterations
        is reached.
        """
        for iteration in range(self.max_iterations):
            logger.info(f"Investigation iteration {iteration + 1}")
            
            self._conduct_investigation_iteration()
            
            if self._is_investigation_complete(iteration):
                self._evaluate_investigation()
                break
        else:
            logger.info("Maximum iterations reached. The case remains unsolved.")

    def _conduct_investigation_iteration(self):

        """
        Conduct a single iteration of the investigation process.

        This method manages the interaction between the Investigator and Referee
        for one round of analysis and clue provision.
        """
        investigator_response = self.investigator.analyze_case()
        logger.info(f"Investigator: {investigator_response}")
        
        # Get the best clue from the referee based on the investigator's response

        if "review the newspapers" in investigator_response.lower():

            if not self.investigator.case_information['newspapers']:
                newspapers = self.referee.provide_newspapers()
                logger.info("Referee: Providing all newspaper articles.")
                investigator_analysis = self.investigator.process_newspapers(newspapers)
                logger.info(f"Investigator's newspaper analysis: {investigator_analysis}")
            else:
                logger.info("Referee: Newspapers have already been provided.")
                self.investigator.get_response("You have already reviewed the newspapers. Please consider the information you've gathered and decide on your next action.")
        else:

            referee_response = self.referee.provide_best_clue(investigator_response)
            logger.info(f"Referee: {referee_response}")
        
            # Process the clue received from the referee
            self._process_clue(referee_response)
        
            # Get the investigator's response to the referee's clue
            self.investigator.get_response(f"The referee said: {referee_response}\nBased on this information, what are your next thoughts or actions?")

    def _process_clue(self, referee_response):

        """
        Process the clue provided by the Referee.

        This method identifies the relevant clue from the Referee's response
        and passes it to the Investigator for processing.

        Args:
            referee_response (str): The response from the Referee containing a clue.
        """

        # Find the clue that matches the referee's response and process it
        for clue in self.referee.clues:
            if clue['location'] in referee_response:
                self.investigator.process_clue(clue)
                break

    def _is_investigation_complete(self, iteration):

        """
        Check if the investigation is complete.

        This method determines whether the Investigator is ready to provide final
        answers or if the maximum number of iterations has been reached.

        Args:
            iteration (int): The current iteration number.

        Returns:
            bool: True if the investigation is complete, False otherwise.
        """
        investigator_response = self.investigator.analyze_case()

        # Check if the investigator is ready to answer or if we've reached the max iterations
        return "ready to answer" in investigator_response.lower() or iteration == self.max_iterations - 1

    def _evaluate_investigation(self):

        """
        Evaluate the results of the investigation.

        This method prompts the Investigator for final answers, passes them to
        the Referee for evaluation, and logs the results.
        """
        referee_prompt = self.referee.ask_for_solution()

        # Get the solution prompt from the referee
        investigator_answers = self.investigator.answer_questions(referee_prompt)

        # Evaluate the investigator's answers
        if investigator_answers:
            evaluation = self.referee.evaluate_answer(investigator_answers)
            logger.info(f"Referee's Evaluation: {evaluation}")
            
            # Log the evaluation results
            self._log_evaluation_results(evaluation)

    def _log_evaluation_results(self, evaluation):

        """
        Log the evaluation results of the investigation.

        This method parses the evaluation JSON and logs detailed results for each
        question as well as the total score.

        Args:
            evaluation (str): A JSON string containing the evaluation results.
        """

        try:

            # Parse the evaluation JSON
            eval_dict = json.loads(evaluation)

            # Calculate and log the total score
            total_score = eval_dict['total_score']
            max_possible_score = sum(question['points'] for question in self.referee.questions)
            logger.info(f"Total Score: {total_score}/{max_possible_score}")
            
            # Log individual question evaluations
            for result in eval_dict['individual_evaluations']:
                logger.info(f"Question: {result['question']}")
                logger.info(f"Evaluation: {result['evaluation']}")
                logger.info(f"Score: {result['score']}/{result['points']}")
                logger.info("---")

        except json.JSONDecodeError:
            logger.error("Failed to parse evaluation results")
