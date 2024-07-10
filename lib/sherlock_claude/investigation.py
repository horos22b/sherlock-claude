"""
This module defines the Investigation class, which orchestrates the entire
sherlock claude process, managing interactions between the Investigator and Referee.

The Investigation class controls the flow of the game, including iterations of
clue provision, analysis, and final evaluation.
"""

from sherlock_claude.referee import Referee
from sherlock_claude.investigator import Investigator
from sherlock_claude.utils import logger, debug_print

import sys
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
        self.max_iterations = 1
        self._investigation_complete = False

    def run(self):

        """
        Run the entire investigation process.

        This method manages the main loop of the investigation, conducting
        iterations until the case is solved or the maximum number of iterations
        is reached.
        """

#        import pdb
#        pdb.set_trace()

        for iteration in range(self.max_iterations):
            logger.info(f"Investigation iteration {iteration + 1}")
            
            self._conduct_investigation_iteration()
            
            if self._is_investigation_complete(iteration):
                self._evaluate_investigation()
                sys.exit(0)

        logger.info("Maximum iterations reached. returning evaluating now\n") 
        self._evaluate_investigation()
        sys.exit(0)

    def _conduct_investigation_iteration(self):

        """
        Conduct a single iteration of the investigation process.

        This method manages the interaction between the Investigator and Referee
        for one round of analysis and clue provision.
        """

        investigator_response = self.investigator.analyze_case()
        
        # Get the best clue from the referee based on the investigator's response

        choice = self.referee.best_choice(investigator_response)

        if "newspapers" in choice:
            newspapers = self.referee.provide_newspapers()
            investigator_analysis = self.investigator.process_newspapers(newspapers)
#           debug_print("Investigator", f"Newspaper analysis:\n{investigator_analysis}")

        elif "solution" in choice:
            self._investigation_complete = True

        else:

            referee_response = self.referee.provide_best_clue(investigator_response)
#           debug_print("Referee", f"Providing clue:\n  description: {referee_response['description']}\n  location: {referee_response['location']}\n  type: {referee_response['type']}")
        
            # Process the clue received from the referee
            self._process_clue(investigator_response, referee_response)
        

    def _process_clue(self, investigator_response, referee_response):

        """
        Process the clue provided by the Referee.

        This method identifies the relevant clue from the Referee's response
        and passes it to the Investigator for processing.

        Args:
            investigator_response (str): The investigator_response that prompted the clue's returning
            referee_response (str): The response from the Referee containing a clue.
        """

        self.investigator.process_clue(investigator_response, referee_response)

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

        if self._investigation_complete:
            return  True

        if iteration == self.max_iterations - 1:
            return True

    def _evaluate_investigation(self):

        """
        Evaluate the results of the investigation.

        This method prompts the Investigator for final answers, passes them to
        the Referee for evaluation, and logs the results.
        """
        referee_prompt = self.referee.ask_for_solution()

        # Get the solution prompt from the referee
        investigator_answers = self.investigator.answer_questions()

        # Evaluate the investigator's answers

#        import pdb
#        pdb.set_trace()

        evaluation = self.referee.evaluate_answer(investigator_answers)
            
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

            fh = open("investigation_results.txt", "w")
            
            # Log individual question evaluations
            for result in eval_dict['individual_evaluations']:

                logger.info(f"Question: {result['question']}")
                logger.info(f"Evaluation: {result['evaluation']}")
                logger.info(f"Score: {result['score']}/{result['points']}")
                logger.info("---")

                fh.write(f"Question: {result['question']}")
                fh.write(f"Evaluation: {result['evaluation']}")
                fh.write(f"Score: {result['score']}/{result['points']}")
                fh.write("---")

            _final_theory = self.investigator.final_theory()
        
            fh.write(f"Investigator's Final Theory:\n{_final_theory}\n\n")
            fh.write(f"Actual Solution:\n{self.referee.solution_data['description']}\n\n")
            fh.write(f"Total Score: {total_score}/{sum(q['points'] for q in self.referee.questions)}")

        except json.JSONDecodeError:

            logger.error("Failed to parse evaluation results")
