# pylint: disable=E0401, W0107, W0718
"""
This module provides functionality to interact with the OpenAI GPT-3.5 Turbo API.

It includes the `AIModel` class, which facilitates communication with the API to generate responses
based on user input. The module loads the OpenAI API key from an environment variable using the
`dotenv` package and uses the `openai` Python library to send requests to the GPT-3.5 Turbo model.

Classes:
    AIModel: A class that interacts with the OpenAI GPT-3.5 Turbo API to generate conversational
             responses based on input text.

Usage:
    - Initialize an `AIModel` instance and use the `get_response()` method to send a user prompt and
      receive an AI-generated response.
    - The OpenAI API key should be provided either directly or via an environment variable named
      "OPENAI_API_KEY".
"""

import os
from dotenv import load_dotenv
import openai

# Set your OpenAI API key here or via an environment variable named "OPENAI_API_KEY"
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class AIModel:
    """
    AIModel class for interacting with the OpenAI GPT-3.5 Turbo API.

    This class allows for generating responses from the ChatGPT API using a
    user-provided input. It initializes the necessary settings and handles API
    requests to generate conversational responses.
    """

    def __init__(self):
        """
        Initializes the AIModel instance.

        This method can be extended to include any additional setup required for the model.
        For now, it simply initializes the instance.
        """
        # Additional initialization can be added here if needed.
        pass

    def get_response(self, input_text):
        """
        Given an input prompt, calls the ChatGPT API using the gpt-3.5-turbo model and
        returns the generated response.
        """
        print(f"Generating response for: {input_text}")

        messages = [
            {"role": "system", "content": "You are a helpful personal trainer."},
            {"role": "user", "content": input_text},
        ]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                max_tokens=600,
                n=1,
                stop=None,
                temperature=0.7,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"Error generating response: {str(e)}"

        return answer


# Instantiate the AI model for use globally
ai_model = AIModel()
