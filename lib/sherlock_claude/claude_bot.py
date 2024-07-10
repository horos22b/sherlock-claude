"""
This module provides a base class for interacting with the Claude API.

The ClaudeBot class handles API communication, message management, and response processing.
It serves as a foundation for more specialized AI agents in the investigation system.
"""

import os
import time
import requests
import json
from sherlock_claude.config import API_KEY, API_URL, MODEL, MAX_TOKENS, ANTHROPIC_VERSION, SHERLOCK_DEBUG, SHERLOCK_LITE_DEBUG
from sherlock_claude.utils import logger, debug_print

class ClaudeBot:

    """
    A base class for creating AI agents that interact with the Claude API.

    This class manages the conversation history, sends requests to the Claude API,
    and processes the responses. It's designed to be subclassed for creating
    specialized AI agents like the Investigator and Referee.

    Attributes:
        role (str): The role of the AI agent (e.g., "investigator", "referee").
        system_message (str): The system message that defines the AI's behavior and context.
        messages (list): A list of message dictionaries representing the conversation history.
        window_size (int): The maximum number of recent messages to include in each API request.
        headers (dict): HTTP headers for API requests, including authentication and API version.

    """

    def __init__(self, role, system_message, window_size=1000):

        """
        Initialize a new ClaudeBot instance.

        Args:
            role (str): The role of the AI agent.
            system_message (str): The system message for the AI.
            window_size (int, optional): The conversation history window size. Defaults to 1000.
        """

        self.role = role
        self.system_message = system_message
        self.messages = []
        self.window_size = window_size
        self.headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": ANTHROPIC_VERSION
        }

    def add_message(self, role, content):

        """
        Add a message to the conversation history.

        Args:
            role (str): The role of the message sender (e.g., "user", "assistant").
            content (str): The content of the message.
        """

        self.messages.append({"role": role, "content": content})

    def get_simple_response(self, prompts):

        """
        Send a simple request to the Claude API and get a response.

        This method makes a simple request out of the given the arguments and passes it 
        to the Claude API.

        Args:
            prompt (list|str): The input prompt to send to the API.

        Returns:
            str: The text content of the API response, or None if an error occurred.
        """

        if isinstance(prompts, str):
            proc_prompts = [ {'role': 'user', 'content': prompts } ]
            
        elif isinstance(prompts, list):
        
            proc_prompts = [ { 'role': 'user', 'content' : _ } for _ in prompts ]

        return self._post_response(proc_prompts)


    def get_response(self, prompt, dryrun=False):

        """
        Send a request to the Claude API and get a response.

        This method adds the prompt to the conversation history, sends a request
        to the Claude API with the recent conversation history, and processes
        the response.

        Args:
            prompt (str): The input prompt to send to the API.
            images (list, optional): A list of base64-encoded images to include in the request.
            dryrun (bool):    just store message or actually send it

        Returns:
            str: The text content of the API response, or None if an error occurred.
        """

        self.add_message("user", prompt)
        windowed_messages = self.messages[-self.window_size:]

        if dryrun:
            return False

        return self._post_response(windowed_messages)
       
    def _post_response(self, windowed_messages):

        data = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": windowed_messages,
            "system": self.system_message
        }

        if SHERLOCK_DEBUG:
            logger.info(f"request: {data}")

        for retry in range(3):

            response = requests.post(API_URL, headers=self.headers, json=data)

            if 'SHERLOCK_DEBUG' in os.environ:
                logger.info(f"response: {response.json()}")
        
            if response.status_code == 200:
                content = response.json()['content'][0]['text']
                self.add_message("assistant", content)
                return content
            else:
                logger.error(f"Error: {response.status_code}")
                logger.error(response.text)

#                import pdb
#                pdb.set_trace()

                time.sleep(5)

            logger.info("retrying...")

        raise Exception("The system is not available")

    def get_retry_simple_response(self, text, eval_func=lambda x: True, process_func=lambda x: x, max_retries=3, print_eval=False):

        for attempt in range(max_retries):

            response = self.get_simple_response(text)

            if print_eval:
                debug_print(print_eval, f"evaled response: {response}")

            try:

                eval_result = eval_func(response)

                if not eval_result:
                    logger.warning(f"retrying {response}")

#                   import pdb
#                   pdb.set_trace()

                    eval_func(response)
                    time.sleep(5)  # Wait for 5 seconds before retrying
                    continue 

                result = process_func(response)

                if result is not None:
                    return result

                else:
                    pass

            except ValueError:
                pass

            if attempt < max_retries - 1:
                time.sleep(5)  # Wait for 5 seconds before retrying
                logger.warning(f"retrying {response}")


        raise ValueError(f"Failed to get a valid response after {max_retries} attempts")

