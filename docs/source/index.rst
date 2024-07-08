Sherlock Claude Documentation
=============================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   case_converter

Welcome to the Sherlock Claude documentation. This project implements an AI-driven detective game or simulation where an AI Investigator tries to solve cases by analyzing clues and formulating theories, while an AI Referee manages the flow of information and evaluates the Investigator's progress.

Getting Started
---------------

To use Sherlock Claude in your project, you can import the necessary modules like this:

.. code-block:: python

   from sherlock_claude import investigation
   from sherlock_claude import config
   from sherlock_claude.utils import load_json

   # Create an investigation
   inv = investigation.Investigation("/path/to/case")
   inv.run()

   # Access config variables
   print(config.API_URL)

   # Use utility functions
   data = load_json("/path/to/file.json")

For more detailed information on each module, please refer to the Modules section in the table of contents.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
