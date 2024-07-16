"""
This module provides a base class for interacting with the Claude API.

The ClaudeBot class handles API communication, message management, and response processing.
It serves as a foundation for more specialized AI agents in the investigation system.
"""

import re
import os
import time
import requests
import json
from sherlock_claude.config import API_KEY, API_URL, MODEL, MAX_TOKENS, ANTHROPIC_VERSION, SHERLOCK_DEBUG, SHERLOCK_LITE_DEBUG
from sherlock_claude.utils import logger, debug_print, gettext, puttext, write_logmode, write_filemode
from sherlock_claude.image_processor import ImageProcessor
from requests.exceptions import ConnectionError, RequestException
from urllib3.exceptions import ProtocolError

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

    def __init__(self, role, system_message, case_directory, window_size=1000):

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
        self.image_processor = ImageProcessor()
        self.image_processor.set_case_directory(case_directory)

    def add_message(self, role, content):

        """
        Add a message to the conversation history.

        Args:
            role (str): The role of the message sender (e.g., "user", "assistant").
            content (str): The content of the message.
        """

        self.messages.append({"role": role, "content": content})

    def get_simple_response(self, prompts, filemode=None,logmode=None):

        """
        Send a simple request to the Claude API and get a response.

        This method makes a simple request out of the given arguments and passes it 
        to the Claude API.

        Args:
            prompts (list|str): The input prompt(s) to send to the API.

        Returns:
            str: The text content of the API response, or None if an error occurred.
        """

        if isinstance(prompts, str):
            proc_prompts = [ {'role': 'user', 'content': prompts } ]
            
        elif isinstance(prompts, list):
        
            proc_prompts = [ { 'role': 'user', 'content' : _ } for _ in prompts ]

        return self._post_response(proc_prompts,filemode=filemode,logmode=logmode)


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

    def _post(self, _url, headers=False, json=False):

        delay = 5
        max_retries = 5
        for attempt in range(max_retries):        

            try:
                response = requests.post(API_URL, headers=self.headers, json=json)
                return response

            except (ConnectionError, ProtocolError) as e:
                if attempt < max_retries - 1:
                    print(f"Connection error occurred: {e}")
                    print(f"Retrying in {delay} seconds... (Attempt {attempt + 1} of {max_retries})")
                    time.sleep(delay * (attempt+1))


        raise "Error in posting."
            
       
    def _post_response(self, windowed_messages,filemode=False,logmode=False):

        data = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": self._prepare_messages_with_images(windowed_messages),
            "system": self.system_message
        }

        if SHERLOCK_DEBUG:
            logger.info(f"request: {data}")

        if filemode:
            return write_filemode(filemode, data)

        for retry in range(5):

            response = self._post(API_URL, headers=self.headers, json=data)

            if SHERLOCK_DEBUG:
                logger.info(f"response: {response.json()}")
        
            if response.status_code == 200:
                content = response.json()['content'][0]['text']
                self.add_message("assistant", content)

                if logmode:
                    write_logmode(logmode, data, content)

                return content

            else:
                logger.error(f"Error: {response.status_code}")
                logger.error(response.text)

                time.sleep(5)

            logger.info("retrying...")

        raise Exception("The system is not available")

    def get_retry_simple_response(self, text, eval_func=lambda x: True, process_func=lambda x: x, max_retries=5, print_eval=False,filemode=False,logmode=False):

        """
        Send a request to the Claude API with retry functionality and custom evaluation.
    
        This method sends a request to the API and retries if the response doesn't meet
        the criteria specified by the evaluation function. It also allows for custom
        processing of the response.
    
        Args:
            text (str): The input text to send to the API.
            eval_func (function, optional): A function to evaluate the API response. Defaults to always return True.
            process_func (function, optional): A function to process the API response. Defaults to identity function.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            print_eval (bool, optional): Whether to print the evaluation result. Defaults to False.
    
        Returns:
            The processed API response if successful, or None if all retries fail.
    
        Raises:
            ValueError: If a valid response cannot be obtained after the maximum number of retries.
        """

        for attempt in range(max_retries):

            response = self.get_simple_response(text,filemode=filemode,logmode=logmode)

            if print_eval:
                debug_print(print_eval, f"evaled response: {response}")

            try:

                eval_result = eval_func(response)

                if not eval_result:

                    logger.warning(f"retrying {response}")

                    eval_func(response)
                    wait_time = 5 * (2 * attempt)  # Exponential backoff
                    time.sleep(wait_time)  # Wait before retrying
                    continue 

                result = process_func(response)

                if result is not None:
                    return result

                else:
                    pass

            except ValueError:
                pass

            if attempt < max_retries - 1:
                wait_time = 5 * (2 ** attempt)  # Exponential backoff
                time.sleep(wait_time)  # Wait before retrying
                logger.warning(f"retrying {response}")


        raise ValueError(f"Failed to get a valid response after {max_retries} attempts")

    def process_case_content(self, content, case_directory):
        """
        Process the case content, handling image tags.

        Args:
            content (str): The case content with image tags.
            case_directory (str): The directory containing case files and images.

        Returns:
            str: Processed content with image tags replaced by indexed references.
        """
        return self.image_processor.process_content(content, case_directory)

    def get_image_info(self, index):
        """
        Get information about a specific image by its index.

        Args:
            index (int): The index of the image.

        Returns:
            str: Formatted string containing image metadata.
        """
        return self.image_processor.get_image_info(index)

    def get_full_image_index(self):
        """
        Get the full image index.

        Returns:
            dict: The complete image index.
        """
        return self.image_processor.get_full_image_index()

    def _prepare_messages_with_images(self, messages):
        prepared_messages = []
        for message in messages:
            prepared_message = {
                "role": message["role"],
                "content": []
            }
            
            # Split the content by image references
            parts = re.split(r'(\[IMAGE:\d+\])', message["content"])
            
            for part in parts:
                if part.startswith("[IMAGE:"):
                    # Extract image index
                    image_index = int(part[7:-1])
                    image_data = self.image_processor.get_image_data(image_index)
                    if image_data:
                        prepared_message["content"].append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_data["media_type"],
                                "data": image_data["data"]
                            }
                        })
                else:
                    if part.strip():
                        prepared_message["content"].append({
                            "type": "text",
                            "text": part
                        })
            
            prepared_messages.append(prepared_message)
        
        return prepared_messages
