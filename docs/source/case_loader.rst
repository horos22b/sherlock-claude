Case Loader Module
==================

.. automodule:: sherlock_claude.case_loader
   :members:
   :undoc-members:
   :show-inheritance:

File Structure
--------------

The CaseLoader expects the following JSON files in the case directory:

- `setup.json`: Contains the initial setup information for the case.
- `clues.json`: Contains a list of all available clues for the case.
- `questions.json`: Contains the list of questions for the case.
- `answers.json`: Contains the correct answers to the case questions.
- `solution.json`: Contains the complete solution to the case.
- `informants.json`: Contains information about informants.
- `newspapers.json`: Contains newspaper articles related to the case.

Usage
-----

To use the CaseLoader, import it from the sherlock_claude package and call its static method with the path to the case directory:

.. code-block:: python

   from sherlock_claude.case_loader import CaseLoader

   case_data = CaseLoader.load_case("/path/to/case/directory")

   setup, clues, questions, answers, solution, informants, newspapers = case_data
