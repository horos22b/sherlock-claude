Config Module
=============

.. automodule:: sherlock_claude.config
   :members:
   :undoc-members:
   :show-inheritance:

Environment Variables
---------------------

The following environment variable should be set in a `.env` file or in your system's environment:

- ``ANTHROPIC_API_KEY``: Your Anthropic API key for authentication.

Usage
-----

To use these configuration settings in your code, import them from the sherlock_claude.config module:

.. code-block:: python

   from sherlock_claude.config import API_KEY, API_URL, MODEL, MAX_TOKENS, ANTHROPIC_VERSION

   # Example usage
   print(f"Using model: {MODEL}")
   print(f"Max tokens: {MAX_TOKENS}")
   print(f"API version: {ANTHROPIC_VERSION}")

Make sure to keep your API key confidential and never commit it to version control.
